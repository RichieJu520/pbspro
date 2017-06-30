# coding: utf-8

# Copyright (C) 1994-2017 Altair Engineering, Inc.
# For more information, contact Altair at www.altair.com.
#
# This file is part of the PBS Professional ("PBS Pro") software.
#
# Open Source License Information:
#
# PBS Pro is free software. You can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# PBS Pro is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Commercial License Information:
#
# The PBS Pro software is licensed under the terms of the GNU Affero General
# Public License agreement ("AGPL"), except where a separate commercial license
# agreement for PBS Pro version 14 or later has been executed in writing with
# Altair.
#
# Altair’s dual-license business model allows companies, individuals, and
# organizations to create proprietary derivative works of PBS Pro and
# distribute them - whether embedded or bundled with other software - under
# a commercial license agreement.
#
# Use of Altair’s trademarks, including but not limited to "PBS™",
# "PBS Professional®", and "PBS Pro™" and Altair’s logos is subject to Altair's
# trademark licensing policies.

from tests.functional import *


class TestEquivClass(TestFunctional):

    """
    Test equivalence class functionality
    """

    def setUp(self):
        TestFunctional.setUp(self)
        a = {'resources_available.ncpus': 8}
        self.server.create_vnodes('vnode', a, 1, self.mom, usenatvnode=True)
        self.scheduler.set_sched_config({'log_filter': 2048})
        # capture the start time of the test for log matching
        self.t = int(time.time())

    def submit_jobs(self, num_jobs=1,
                    attrs={'Resource_List.select': '1:ncpus=1'},
                    user=TEST_USER):
        """
        Submit num_jobs number of jobs with attrs attributes for user.
        Return a list of job ids
        """
        ret_jids = []
        for n in range(num_jobs):
            J = Job(user, attrs)
            jid = self.server.submit(J)
            ret_jids += [jid]

        return ret_jids

    def test_basic(self):
        """
        Test the basic behavior of job equivalence classes: submit two
        different types of jobs and see they are in two different classes
        """
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        jids1 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=4'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

    def test_select(self):
        """
        Test to see if jobs with select resources not in the resources line
        fall into the same equivalence class
        """
        self.server.manager(MGR_CMD_CREATE, RSC,
                            {'type': 'long', 'flag': 'nh'}, id='foo')

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        a = {'Resource_List.select': '1:ncpus=1:foo=4'}
        jids1 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=1:foo=8'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Two equivalence classes: one for the resource eating job and one
        # for the other two jobs. While jobs have different amounts of
        # the foo resource, foo is not on the resources line.
        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

    def test_place(self):
        """
        Test to see if jobs with different place statements
        fall into the different equivalence classes
        """
        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        a = {'Resource_List.select': '1:ncpus=1',
             'Resource_List.place': 'free'}
        jids1 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=1',
             'Resource_List.place': 'excl'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes: one for the resource eating job and
        # one for each place statement
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_reslist1(self):
        """
        Test to see if jobs with resources in Resource_List that are not in
        the sched_config resources line fall into the same equivalence class
        """
        self.server.manager(MGR_CMD_CREATE, RSC, {'type': 'string'},
                            id='baz')
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        a = {'Resource_List.software': 'foo'}
        jids1 = self.submit_jobs(3, a)

        a = {'Resource_List.software': 'bar'}
        jids2 = self.submit_jobs(3, a)

        a = {'Resource_List.baz': 'foo'}
        jids1 = self.submit_jobs(3, a)

        a = {'Resource_List.baz': 'bar'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Two equivalence classes.  One for the resource eating job and
        # one for the rest.  The rest of the jobs have differing values of
        # resources not on the resources line.  They fall into one class.
        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

    def test_reslist2(self):
        """
        Test to see if jobs with resources in Resource_List that are in the
        sched_config resources line fall into the different equivalence classes
        """
        self.server.manager(MGR_CMD_CREATE, RSC, {'type': 'string'},
                            id='baz')

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})
        self.scheduler.add_resource('software')
        self.scheduler.add_resource('baz')

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        a = {'Resource_List.software': 'foo'}
        jids1 = self.submit_jobs(3, a)

        a = {'Resource_List.software': 'bar'}
        jids2 = self.submit_jobs(3, a)

        a = {'Resource_List.baz': 'foo'}
        jids3 = self.submit_jobs(3, a)

        a = {'Resource_List.baz': 'bar'}
        jids4 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each value of software and baz.
        self.scheduler.log_match("Number of job equivalence classes: 5",
                                 max_attempts=10, starttime=self.t)

    def test_nolimits(self):
        """
        Test to see that jobs from different users, groups, and projects
        all fall into the same equivalence class when there are no limits
        """
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        jids1 = self.submit_jobs(3, user=TEST_USER)
        jids2 = self.submit_jobs(3, user=TEST_USER2)

        b = {'group_list': TSTGRP1, 'Resource_List.select': '1:ncpus=8'}
        jids3 = self.submit_jobs(3, a, TEST_USER1)

        b = {'group_list': TSTGRP2, 'Resource_List.select': '1:ncpus=8'}
        jids4 = self.submit_jobs(3, a, TEST_USER1)

        b = {'project': 'p1', 'Resource_List.select': '1:ncpus=8'}
        jids5 = self.submit_jobs(3, a)

        b = {'project': 'p2', 'Resource_List.select': '1:ncpus=8'}
        jids6 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Two equivalence classes: one for the resource eating job and one
        # for the rest.  Since there are no limits, user, group, nor project
        # are taken into account
        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

    def test_user(self):
        """
        Test to see that jobs from different users fall into the same
        equivalence class without user limits set
        """
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        jids1 = self.submit_jobs(3, user=TEST_USER)
        jids2 = self.submit_jobs(3, user=TEST_USER2)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Two equivalence classes: One for the resource eating job and
        # one for the rest.  Since there are no limits, both users are
        # in one class.
        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

    def test_user_old(self):
        """
        Test to see that jobs from different users fall into different
        equivalence classes with old style limits set
        """
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'max_user_run': 4})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        jids1 = self.submit_jobs(3, user=TEST_USER)
        jids2 = self.submit_jobs(3, user=TEST_USER2)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job
        # and one for each user.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_user_server(self):
        """
        Test to see that jobs from different users fall into different
        equivalence classes with server hard limits set
        """
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'max_run': '[u:PBS_GENERIC=4]'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        jids1 = self.submit_jobs(3, user=TEST_USER)
        jids2 = self.submit_jobs(3, user=TEST_USER2)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job
        # and one for each user.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_user_server_soft(self):
        """
        Test to see that jobs from different users fall into different
        equivalence classes with server soft limits set
        """
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'max_run_soft': '[u:PBS_GENERIC=4]'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        jids1 = self.submit_jobs(3, user=TEST_USER)
        jids2 = self.submit_jobs(3, user=TEST_USER2)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each user.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_user_queue(self):
        """
        Test to see that jobs from different users fall into different
        equivalence classes with queue limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'max_run': '[u:PBS_GENERIC=4]'}, id='workq')

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        jids1 = self.submit_jobs(3, user=TEST_USER)
        jids2 = self.submit_jobs(3, user=TEST_USER2)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each user.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_user_queue_soft(self):
        """
        Test to see that jobs from different users fall into different
        equivalence classes with queue soft limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'max_run_soft': '[u:PBS_GENERIC=4]'}, id='workq')

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER, attrs=a)
        self.server.submit(J)

        jids1 = self.submit_jobs(3, user=TEST_USER)
        jids2 = self.submit_jobs(3, user=TEST_USER2)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each user.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_group(self):
        """
        Test to see that jobs from different groups fall into the same
        equivalence class without group limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'group_list': TSTGRP1}
        jids1 = self.submit_jobs(3, a, TEST_USER1)

        a = {'group_list': TSTGRP2}
        jids2 = self.submit_jobs(3, a, TEST_USER1)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Two equivalence classes: One for the resource eating job and
        # one for the rest.  Since there are no limits, both groups are
        # in one class.
        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

    def test_group_old(self):
        """
        Test to see that jobs from different groups fall into different
        equivalence class old style group limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'max_group_run': 4})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'group_list': TSTGRP1}
        jids1 = self.submit_jobs(3, a, TEST_USER1)

        a = {'group_list': TSTGRP2}
        jids2 = self.submit_jobs(3, a, TEST_USER1)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each group.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_group_server(self):
        """
        Test to see that jobs from different groups fall into different
        equivalence class server group limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'max_run': '[g:PBS_GENERIC=4]'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'group_list': TSTGRP1}
        jids1 = self.submit_jobs(3, a, TEST_USER1)

        a = {'group_list': TSTGRP2}
        jids2 = self.submit_jobs(3, a, TEST_USER1)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each group.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_group_server_soft(self):
        """
        Test to see that jobs from different groups fall into different
        equivalence class server soft group limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'max_run_soft': '[g:PBS_GENERIC=4]'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'group_list': TSTGRP1}
        jids1 = self.submit_jobs(3, a, TEST_USER1)

        a = {'group_list': TSTGRP2}
        jids2 = self.submit_jobs(3, a, TEST_USER1)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each group.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_group_queue(self):
        """
        Test to see that jobs from different groups fall into different
        equivalence class queue group limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'max_run': '[g:PBS_GENERIC=4]'}, id='workq')

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'group_list': TSTGRP1}
        jids1 = self.submit_jobs(3, a, TEST_USER1)

        a = {'group_list': TSTGRP2}
        jids2 = self.submit_jobs(3, a, TEST_USER1)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each group.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_group_queue_soft(self):
        """
        Test to see that jobs from different groups fall into different
        equivalence class queue group soft limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'max_run_soft': '[g:PBS_GENERIC=4]'}, id='workq')

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'group_list': TSTGRP1}
        jids1 = self.submit_jobs(3, a, TEST_USER1)

        a = {'group_list': TSTGRP2}
        jids2 = self.submit_jobs(3, a, TEST_USER1)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each group.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_proj(self):
        """
        Test to see that jobs from different projects fall into the same
        equivalence class without project limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'project': 'p1'}
        jids1 = self.submit_jobs(3, a)

        a = {'project': 'p2'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Two equivalence classes: One for the resource eating job and
        # one for the rest.  Since there are no limits, both projects are
        # in one class.
        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

    def test_proj_server(self):
        """
        Test to see that jobs from different projects fall into different
        equivalence classes with server project limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'max_run': '[p:PBS_GENERIC=4]'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'project': 'p1'}
        jids1 = self.submit_jobs(3, a)

        a = {'project': 'p2'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each project.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_proj_server_soft(self):
        """
        Test to see that jobs from different projects fall into different
        equivalence class server project soft limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'max_run_soft': '[p:PBS_GENERIC=4]'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'project': 'p1'}
        jids1 = self.submit_jobs(3, a)

        a = {'project': 'p2'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each project.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_proj_queue(self):
        """
        Test to see that jobs from different groups fall into different
        equivalence class queue project limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'max_run': '[p:PBS_GENERIC=4]'}, id='workq')

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'project': 'p1'}
        jids1 = self.submit_jobs(3, a)

        a = {'project': 'p2'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each project.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_proj_queue_soft(self):
        """
        Test to see that jobs from different groups fall into different
        equivalence class queue project soft limits set
        """

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'max_run_soft': '[p:PBS_GENERIC=4]'}, id='workq')

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'project': 'p1'}
        jids1 = self.submit_jobs(3, a)

        a = {'project': 'p2'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one for each project.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_queue(self):
        """
        Test to see that jobs from different generic queues fall into
        the same equivalence class
        """

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True'}, id='workq2')

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'priority': 120}, id='workq')

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'queue': 'workq'}
        jids1 = self.submit_jobs(3, a)

        a = {'queue': 'workq2'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Two equivalence classes.  One for the resource eating job and
        # one for the rest.  There is nothing to differentiate the queues
        # so all jobs are in one class.
        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

    def test_queue_limits(self):
        """
        Test to see if jobs in a queue with limits use their queue as part
        of what defines their equivalence class.
        """

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True'}, id='workq2')

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True'}, id='limits1')

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True'}, id='limits2')

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'priority': 120}, id='workq')

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'max_run': '[o:PBS_ALL=20]'}, id='limits1')

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'max_run_soft': '[o:PBS_ALL=20]'}, id='limits2')

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'queue': 'workq'}
        jids1 = self.submit_jobs(3, a)

        a = {'queue': 'workq2'}
        jids2 = self.submit_jobs(3, a)

        a = {'queue': 'limits1'}
        jids3 = self.submit_jobs(3, a)

        a = {'queue': 'limits2'}
        jids4 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # 4 equivalence classes.  One for the resource eating job and
        # One for the queues without limits and one
        # each for the two queues with limits.
        self.scheduler.log_match("Number of job equivalence classes: 4",
                                 max_attempts=10, starttime=self.t)

    def test_queue_nodes(self):
        """
        Test to see if jobs that are submitted into a queue with nodes
        associated with it fall into their own equivalence class
        """

        a = {'resources_available.ncpus': 8}
        self.server.create_vnodes('vnode', a, 2, self.mom, usenatvnode=True)

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True', 'priority': 100}, id='workq2')

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True'}, id='nodes_queue')

        self.server.manager(MGR_CMD_SET, NODE,
                            {'queue': 'nodes_queue'}, id='vnode[0]')

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'priority': 120}, id='workq')

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources on the normal node
        a = {'Resource_List.select': '1:ncpus=8', 'queue': 'workq'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        # Eat up all the resources on node associated to nodes_queue
        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'nodes_queue'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'workq'}
        jids1 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'workq2'}
        jids2 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'nodes_queue'}
        jids3 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes.  One for the resource eating job and
        # one class for the queue with nodes associated with it.
        # One class for normal queues.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

        self.server.manager(MGR_CMD_UNSET, NODE, 'queue',
                            id='vnode[0]')

    def test_prime_queue(self):
        """
        Test to see if a job in a primetime queue has its queue be part of
        what defines its equivalence class.  Also see that jobs in anytime
        queues do not use queue as part of what determines their class
        """

        # Force primetime
        self.scheduler.holidays_set_day("weekday", prime="all",
                                        nonprime="none")
        self.scheduler.holidays_set_day("saturday", prime="all",
                                        nonprime="none")
        self.scheduler.holidays_set_day("sunday", prime="all",
                                        nonprime="none")

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True', 'priority': 100},
                            id='anytime1')
        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True'}, id='anytime2')

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True', 'priority': 100},
                            id='p_queue1')
        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True'}, id='p_queue2')

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'priority': 120}, id='workq')

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8', 'queue': 'workq'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'anytime1'}
        jids1 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'anytime2'}
        jids2 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'p_queue1'}
        jids3 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'p_queue2'}
        jids4 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Four equivalence classes.  One for the resource eating job and
        # one for the normal queues and one for each prime time queue
        self.scheduler.log_match("Number of job equivalence classes: 4",
                                 max_attempts=10, starttime=self.t)

    def test_non_prime_queue(self):
        """
        Test to see if a job in a non-primetime queue has its queue be part of
        what defines its equivalence class.  Also see that jobs in anytime
        queues do not use queue as part of what determines their class
        """

        # Force non-primetime
        self.scheduler.holidays_set_day("weekday", prime="none",
                                        nonprime="all")
        self.scheduler.holidays_set_day("saturday", prime="none",
                                        nonprime="all")
        self.scheduler.holidays_set_day("sunday", prime="none",
                                        nonprime="all")

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True', 'priority': 100},
                            id='anytime1')
        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True'}, id='anytime2')

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True', 'priority': 100},
                            id='np_queue1')

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True'}, id='np_queue2')

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'priority': 120}, id='workq')

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8', 'queue': 'workq'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'anytime1'}
        jids1 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'anytime2'}
        jids2 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'np_queue1'}
        jids3 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=4', 'queue': 'np_queue2'}
        jids4 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Four equivalence classes.  One for the resource eating job and
        # one for the normal queues and one for each non-prime time queue
        self.scheduler.log_match("Number of job equivalence classes: 4",
                                 max_attempts=10, starttime=self.t)

    def test_ded_time_queue(self):
        """
        Test to see if a job in a dedicated time queue has its queue be part
        of what defines its equivalence class.  Also see that jobs in anytime
        queues do not use queue as part of what determines their class
        """

        # Force dedicated time
        now = time.time()
        self.scheduler.add_dedicated_time(start=now - 5, end=now + 3600)

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True', 'priority': 100},
                            id='ded_queue1')

        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True', 'priority': 100},
                            id='ded_queue2')

        self.server.manager(MGR_CMD_SET, QUEUE,
                            {'priority': 120}, id='workq')

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8', 'queue': 'workq'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        a = {'Resource_List.select': '1:ncpus=4',
             'Resource_List.walltime': 600, 'queue': 'ded_queue1'}
        jids1 = self.submit_jobs(3, a)

        a = {'Resource_List.select': '1:ncpus=4',
             'Resource_List.walltime': 600, 'queue': 'ded_queue2'}
        jids2 = self.submit_jobs(3, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes: One for the resource eating job and
        # one for each dedicated time queue job
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_job_array(self):
        """
        Test that various job types will fall into single equivalence
        class with same type of request.
        """

        # Eat up all the resources
        a = {'Resource_List.select': '1:ncpus=8', 'queue': 'workq'}
        J = Job(TEST_USER1, attrs=a)
        self.server.submit(J)

        # Submit a job array
        j = Job(TEST_USER)
        j.set_attributes(
            {ATTR_J: '1-3:1',
             'Resource_List.select': '1:ncpus=8',
             'queue': 'workq'})
        jid = self.server.submit(j)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # One equivalence class
        self.scheduler.log_match("Number of job equivalence classes: 1",
                                 max_attempts=10, starttime=self.t)

    def test_reservation(self):
        """
        Test that similar jobs inside reservations falls under same
        equivalence class.
        """

        # Submit a reservation
        a = {'Resource_List.select': '1:ncpus=3',
             'reserve_start': int(time.time()) + 10,
             'reserve_end': int(time.time()) + 300, }
        r = Reservation(TEST_USER, a)
        rid = self.server.submit(r)
        a = {'reserve_state': (MATCH_RE, "RESV_CONFIRMED|2")}
        self.server.expect(RESV, a, id=rid)

        rname = rid.split('.')
        # Submit jobs inside reservation
        a = {ATTR_queue: rname[0]}
        jids1 = self.submit_jobs(3, a)

        # Submit jobs outside of reservations
        jids2 = self.submit_jobs(3)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Two equivalence classes: one for jobs inside reservations
        # and one for regular jobs
        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

    def test_time_limit(self):
        """
        Test that various time limits will have their own
        equivalence classes
        """

        # Submit a reservation
        a = {'Resource_List.select': '1:ncpus=8',
             'reserve_start': time.time() + 30,
             'reserve_end': time.time() + 300, }
        r = Reservation(TEST_USER, a)
        rid = self.server.submit(r)
        a = {'reserve_state': (MATCH_RE, "RESV_CONFIRMED|2")}
        self.server.expect(RESV, a, id=rid)

        rname = rid.split('.')

        # Submit jobs with cput limit inside reservation
        a = {'Resource_List.cput': '20', ATTR_queue: rname[0]}
        jid1 = self.submit_jobs(2, a)

        # Submit jobs with min and max walltime inside reservation
        a = {'Resource_List.min_walltime': '20',
             'Resource_List.max_walltime': '200',
             ATTR_queue: rname[0]}
        jid2 = self.submit_jobs(2, a)

        # Submit jobs with regular walltime inside reservation
        a = {'Resource_List.walltime': '20', ATTR_queue: rname[0]}
        jid3 = self.submit_jobs(2, a)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes: one for each job set
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_fairshare(self):
        """
        Test that scheduler do not create any equiv classes
        if fairshare is set
        """

        a = {'fair_share': 'true ALL',
             'fairshare_usage_res': 'ncpus*walltime',
             'unknown_shares': 10}
        self.scheduler.set_sched_config(a)

        # Submit jobs as different user
        jid1 = self.submit_jobs(8, user=TEST_USER1)
        jid2 = self.submit_jobs(8, user=TEST_USER2)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # One equivalence class
        self.scheduler.log_match("Number of job equivalence classes: 1",
                                 max_attempts=10, starttime=self.t)

        # Wait sometime for jobs to accumulate walltime
        time.sleep(20)

        # Submit another job
        self.t = int(time.time())
        jid3 = self.submit_jobs(1, user=TEST_USER3)

        # Look at the job equivalence classes again
        self.scheduler.log_match("Number of job equivalence classes: 1",
                                 max_attempts=10,
                                 starttime=self.t)

    def test_server_hook(self):
        """
        Test that job equivalence classes are updated
        when job attributes get updated by hooks
        """

        # Define a queuejob hook
        hook1 = """
import pbs
e = pbs.event()
e.job.Resource_List["walltime"] = 200
"""

        # Define a runjob hook
        hook2 = """
import pbs
e = pbs.event()
e.job.Resource_List["cput"] = 40
"""

        # Define a modifyjob hook
        hook3 = """
import pbs
e = pbs.event()
e.job.Resource_List["cput"] = 20
"""

        # Create a queuejob hook
        a = {'event': 'queuejob', 'enabled': 'True'}
        self.server.create_import_hook("t_q", a, hook1)

        # Create a runjob hook
        a = {'event': 'runjob', 'enabled': 'True'}
        self.server.create_import_hook("t_r", a, hook2)

        # Create a modifyjob hook
        a = {'event': 'modifyjob', 'enabled': 'True'}
        self.server.create_import_hook("t_m", a, hook3)

        # Turn scheduling off
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Submit jobs as different users
        a = {'Resource_List.ncpus': 2}
        jid1 = self.submit_jobs(4, a, user=TEST_USER1)
        jid2 = self.submit_jobs(4, a, user=TEST_USER2)
        jid3 = self.submit_jobs(4, a, user=TEST_USER3)

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # One equivalence class
        self.scheduler.log_match("Number of job equivalence classes: 1",
                                 max_attempts=10, starttime=self.t)

        # Alter a queued job
        self.t = int(time.time())
        self.server.alterjob(jid3[2], {ATTR_N: "test"})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence classes: one is for queued jobs that
        # do not have cput set. 2 for the different cputime value
        # set by runjob and modifyjob hook
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10,
                                 starttime=self.t)

    def test_mom_hook(self):
        """
        Test for job equivalence classes with mom hooks.
        """

        # Create resource
        attrib = {}
        attrib['type'] = "string_array"
        attrib['flag'] = 'h'
        self.server.manager(MGR_CMD_CREATE, RSC, attrib, id='foo_str')

        # Create vnodes
        a = {'resources_available.ncpus': 4,
             'resources_available.foo_str': "foo,bar,buba"}
        self.server.create_vnodes('vnode', a, 4, self.mom)

        # Add resources to sched_config
        self.scheduler.add_resource("foo_str")

        # Create execjob_begin hook
        hook1 = """
import pbs
e = pbs.event()
j = e.job

if j.Resource_List["host"] == "vnode[0]":
    j.Resource_List["foo_str"] = "foo"
elif j.Resource_List["host"] == "vnode[1]":
    j.Resource_List["foo_str"] = "bar"
else:
    j.Resource_List["foo_str"] = "buba"
"""

        a = {'event': "execjob_begin", 'enabled': 'True'}
        self.server.create_import_hook("test", a, hook1)

        # Turn off the scheduling
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'False'})

        # Submit jobs
        a = {'Resource_List.select': "vnode=vnode[0]:ncpus=2"}
        jid1 = self.submit_jobs(2, a)
        a = {'Resource_List.select': "vnode=vnode[1]:ncpus=2"}
        jid2 = self.submit_jobs(2, a)
        a = {'Resource_List.select': "vnode=vnode[2]:ncpus=2"}
        jid3 = self.submit_jobs(2, a)

        # Turn on the scheduling
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Three equivalence class for each string value
        # set by mom_hook
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

    def test_incr_decr(self):
        """
        Test for varying job equivalence class values
        """

        # Submit a job
        j = Job(TEST_USER,
                attrs={'Resource_List.select': '1:ncpus=8',
                       'Resource_List.walltime': '20'})
        jid1 = self.server.submit(j)

        # One equivalance class
        self.scheduler.log_match("Number of job equivalence classes: 1",
                                 max_attempts=10, starttime=self.t)

        # Submit another job
        self.t = int(time.time())
        j = Job(TEST_USER,
                attrs={'Resource_List.select': '1:ncpus=8',
                       'Resource_List.walltime': '30'})
        jid2 = self.server.submit(j)

        # Two equivalence classes
        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

        # Submit another job
        self.t = int(time.time())
        j = Job(TEST_USER,
                attrs={'Resource_List.select': '1:ncpus=8',
                       'Resource_List.walltime': '40'})
        jid3 = self.server.submit(j)

        # Three equivalence classes
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

        # Delete job1
        self.server.delete(jid1, wait='True')

        # Rerun scheduling cycle
        self.t = int(time.time())
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # Two equivalence classes
        self.scheduler.log_match("Number of job equivalence classes: 2",
                                 max_attempts=10, starttime=self.t)

        # Delete job2
        self.server.delete(jid2, wait='true')

        # Rerun scheduling cycle
        self.t = int(time.time())
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # One equivalence classes
        self.scheduler.log_match("Number of job equivalence classes: 1",
                                 max_attempts=10, starttime=self.t)

        # Delete job3
        self.server.delete(jid3, wait='true')

        time.sleep(1)  # adding delay to avoid race condition
        # Rerun scheduling cycle
        self.t = int(time.time())
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'scheduling': 'True'})

        # No message for equivalence class
        self.scheduler.log_match("Number of job equivalence classes",
                                 max_attempts=10,
                                 starttime=self.t,
                                 existence=False)
        self.logger.info(
            "Number of job equivalence classes message " +
            "not present when there are no jobs as expected")

    def test_server_queue_limit(self):
        """
        Test with mix of hard and soft limits
        on resources for users and groups
        """

        # Create workq2
        self.server.manager(MGR_CMD_CREATE, QUEUE,
                            {'queue_type': 'e', 'started': 'True',
                             'enabled': 'True'}, id='workq2')

        # Set queue limit
        a = {
            'max_run': '[o:PBS_ALL=100],[g:PBS_GENERIC=20],\
                       [u:PBS_GENERIC=20],[g:tstgrp01 = 8],[u:pbsuser1=10]'}
        self.server.manager(MGR_CMD_SET, QUEUE,
                            a, id='workq2')

        a = {'max_run_res.ncpus':
             '[o:PBS_ALL=100],[g:PBS_GENERIC=50],\
             [u:PBS_GENERIC=20],[g:tstgrp01=13],[u:pbsuser1=12]'}
        self.server.manager(MGR_CMD_SET, QUEUE, a, id='workq2')

        a = {'max_run_res_soft.ncpus':
             '[o:PBS_ALL=100],[g:PBS_GENERIC=30],\
             [u:PBS_GENERIC=10],[g:tstgrp01=10],[u:pbsuser1=10]'}
        self.server.manager(MGR_CMD_SET, QUEUE, a, id='workq2')

        # Create server limits
        a = {
            'max_run': '[o:PBS_ALL=100],[g:PBS_GENERIC=50],\
            [u:PBS_GENERIC=20],[g:tstgrp01=13],[u:pbsuser1=13]'}
        self.server.manager(MGR_CMD_SET, SERVER, a)

        a = {'max_run_soft':
             '[o:PBS_ALL=50],[g:PBS_GENERIC=25],[u:PBS_GENERIC=10],\
             [g:tstgrp01=10],[u:pbsuser1=10]'}
        self.server.manager(MGR_CMD_SET, SERVER, a)

        # Turn scheduling off
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'false'})

        # Submit jobs as pbsuser1 from group tstgrp01 in workq2
        a = {'Resource_List.select': '1:ncpus=1',
             'group_list': TSTGRP1, ATTR_q: 'workq2'}
        jid1 = self.submit_jobs(10, a, TEST_USER1)

        # Submit jobs as pbsuser1 from group tstgrp02 in workq2
        a = {'Resource_List.select': '1:ncpus=1',
             'group_list': TSTGRP2, ATTR_q: 'workq2'}
        jid2 = self.submit_jobs(10, a, TEST_USER1)

        # Submit jobs as pbsuser2 from tstgrp01 in workq2
        a = {'Resource_List.select': '1:ncpus=1',
             'group_list': TSTGRP1, ATTR_q: 'workq2'}
        jid3 = self.submit_jobs(10, a, TEST_USER2)

        # Submit jobs as pbsuser2 from tstgrp03 in workq2
        a = {'Resource_List.select': '1:ncpus=1',
             'group_list': TSTGRP3, ATTR_q: 'workq2'}
        jid4 = self.submit_jobs(10, a, TEST_USER2)

        # Submit jobs as pbsuser1 from tstgrp01 in workq
        a = {'Resource_List.select': '1:ncpus=1',
             'group_list': TSTGRP1, ATTR_q: 'workq'}
        jid5 = self.submit_jobs(10, a, TEST_USER1)

        # Submit jobs as pbsuser1 from tstgrp02 in workq
        a = {'Resource_List.select': '1:ncpus=1',
             'group_list': TSTGRP2, ATTR_q: 'workq'}
        jid6 = self.submit_jobs(10, a, TEST_USER1)

        # Submit jobs as pbsuser2 from tstgrp01 in workq
        a = {'Resource_List.select': '1:ncpus=1',
             'group_list': TSTGRP1, ATTR_q: 'workq'}
        jid7 = self.submit_jobs(10, a, TEST_USER2)

        # Submit jobs as pbsuser2 from tstgrp03 in workq
        a = {'Resource_List.select': '1:ncpus=1',
             'group_list': TSTGRP3, ATTR_q: 'workq'}
        jid8 = self.submit_jobs(10, a, TEST_USER2)

        self.t = int(time.time())

        # Run only one cycle
        self.server.manager(MGR_CMD_SET, MGR_OBJ_SERVER,
                            {'scheduling': 'True'})
        self.server.manager(MGR_CMD_SET, MGR_OBJ_SERVER,
                            {'scheduling': 'False'})

        # Eight equivalence classes; one for each combination of
        # users and groups
        self.scheduler.log_match("Number of job equivalence classes: 8",
                                 max_attempts=10, starttime=self.t)

    def test_preemption(self):
        """
        Test preemption in two cycles.  The first cycle is to preempt a job.
        The second cycle is to make sure jobs that were in the preempted job's
        class are not affected by the fact that the preempted job can't run
        """

        a = {'resources_available.ncpus': 1}
        self.server.create_vnodes('vnode', a, 4, self.mom, usenatvnode=True)

        a = {'queue_type': 'e', 'started': 't',
             'enabled': 't', 'priority': 150}
        self.server.manager(MGR_CMD_CREATE, QUEUE, a, id='expressq')

        a = {'Resource_List.ncpus': 1}
        J = Job(TEST_USER, attrs=a)
        jid1 = self.server.submit(J)
        jid2 = self.server.submit(J)
        self.server.expect(JOB, {'job_state': 'R'}, id=jid1)
        self.server.expect(JOB, {'job_state': 'R'}, id=jid2)

        a = {'Resource_List.ncpus': 3, 'queue': 'expressq'}
        Je = Job(TEST_USER, attrs=a)
        jid3 = self.server.submit(Je)
        self.server.expect(JOB, {'job_state': 'S'}, id=jid1)
        self.server.expect(JOB, {'job_state': 'R'}, id=jid2)
        self.server.expect(JOB, {'job_state': 'R'}, id=jid3)

        jid4 = self.server.submit(J)
        self.server.expect(JOB, 'comment', op=SET)
        self.server.expect(JOB, {'job_state': 'Q'}, id=jid4)

        # 3 equivalence classes: 1 for jid2 and jid4; 1 for jid3; and 1 for
        # jid1 by itself because it is suspended.
        self.scheduler.log_match("Number of job equivalence classes: 3",
                                 max_attempts=10, starttime=self.t)

        self.server.deljob(jid2, wait=True)

        self.server.expect(JOB, {'job_state': 'R'}, id=jid4)
