# This file is a part of datanommer, a message sink for fedmsg.
# Copyright (C) 2014, Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
import json
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import fedmsg.config
from sqlalchemy.orm import scoped_session

import datanommer.commands
import datanommer.models as m


filename = ":memory:"


class TestCommands(unittest.TestCase):
    def setUp(self):
        uri = "sqlite:///%s" % filename
        self.config = {"datanommer.sqlalchemy.url": uri, "logging": {"version": 1}}
        self.config.update(fedmsg.config.load_config())
        m.session = scoped_session(m.maker)
        m.init(uri=uri, create=True)

    def tearDown(self):
        m.session.rollback()
        engine = m.session.get_bind()
        m.DeclarativeBase.metadata.drop_all(engine)
        m._users_seen = set()
        m._packages_seen = set()

    def test_stats(self):
        with patch("datanommer.commands.StatsCommand.get_config") as gc:
            self.config["topic"] = False
            gc.return_value = self.config

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                category="git",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create",
                category="fas",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                category="git",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.StatsCommand()

            command.log.info = info
            command.run()

            assert "git has 2 entries" in logged_info
            assert "fas has 1 entries" in logged_info

    def test_stats_topics(self):
        with patch("datanommer.commands.StatsCommand.get_config") as gc:
            self.config["topic"] = True
            gc.return_value = self.config

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                category="git",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create",
                category="fas",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                category="git",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.StatsCommand()

            command.log.info = info
            command.run()

            assert (
                "org.fedoraproject.prod.git.receive.valgrind.master has 1 entries"
                in logged_info
            )
            assert "org.fedoraproject.stg.fas.user.create has 1 entries" in logged_info
            assert (
                "org.fedoraproject.prod.git.branch.valgrind.master has 1 entries"
                in logged_info
            )

    def test_stats_cat_topics(self):
        with patch("datanommer.commands.StatsCommand.get_config") as gc:
            self.config["topic"] = True
            self.config["category"] = "git"
            gc.return_value = self.config

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                category="git",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create",
                category="fas",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                category="git",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.StatsCommand()

            command.log.info = info
            command.run()

            assert (
                "org.fedoraproject.prod.git.receive.valgrind.master has 1 entries"
                in logged_info
            )
            assert (
                "org.fedoraproject.stg.fas.user.create has 1 entries" not in logged_info
            )
            assert (
                "org.fedoraproject.prod.git.branch.valgrind.master has 1 entries"
                in logged_info
            )

    def test_dump(self):
        m.Message = datanommer.models.Message
        now = datetime.utcnow()

        msg1 = m.Message(
            topic="org.fedoraproject.prod.git.branch.valgrind.master", timestamp=now
        )

        msg2 = m.Message(
            topic="org.fedoraproject.prod.git.receive.valgrind.master", timestamp=now
        )

        msg1.msg = "Message 1"
        msg2.msg = "Message 2"
        objects = [msg1, msg2]

        models = [m.Message]

        with patch("datanommer.models.models", models):
            with patch("datanommer.models.Message.query"):
                m.Message.query.all = Mock(return_value=objects)

                with patch("datanommer.commands.DumpCommand.get_config") as gc:
                    gc.return_value = self.config

                    command = datanommer.commands.DumpCommand()

                    logged_info = []

                    def info(data):
                        logged_info.append(data)

                    command.log.info = info
                    command.run()

                    json_object = json.loads(logged_info[0])

                    assert (
                        json_object[0]["topic"]
                        == "org.fedoraproject.prod.git.branch.valgrind.master"
                    )

    def test_dump_before(self):
        m.Message = datanommer.models.Message

        with patch("datanommer.commands.DumpCommand.get_config") as gc:
            self.config["before"] = "2013-02-16"
            gc.return_value = self.config

            time1 = datetime(2013, 2, 14)
            time2 = datetime(2013, 2, 15)
            time3 = datetime(2013, 2, 16, 8)

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                timestamp=time1,
                i=4,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                timestamp=time2,
                i=3,
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.log.receive.valgrind.master",
                timestamp=time3,
                i=2,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.DumpCommand()

            command.log.info = info
            with patch("datanommer.commands.datetime") as mock_dt:
                mock_dt.utcnow.return_value = datetime(2013, 3, 1)
                mock_dt.now.return_value = datetime(2013, 3, 1)
                command.run()

            json_object = json.loads(logged_info[0])

            assert (
                json_object[0]["topic"]
                == "org.fedoraproject.prod.git.branch.valgrind.master"
            )
            assert (
                json_object[1]["topic"]
                == "org.fedoraproject.prod.git.receive.valgrind.master"
            )
            assert len(json_object) == 2

    def test_dump_since(self):
        with patch("datanommer.commands.DumpCommand.get_config") as gc:
            self.config["since"] = "2013-02-14T08:00:00"
            gc.return_value = self.config

            time1 = datetime(2013, 2, 14)
            time2 = datetime(2013, 2, 15)
            time3 = datetime(2013, 2, 16, 8)

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                timestamp=time1,
                i=4,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                timestamp=time2,
                i=3,
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.log.receive.valgrind.master",
                timestamp=time3,
                i=2,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.DumpCommand()

            command.log.info = info
            with patch("datanommer.commands.datetime") as mock_dt:
                mock_dt.utcnow.return_value = datetime(2013, 3, 1)
                mock_dt.now.return_value = datetime(2013, 3, 1)
                command.run()

            json_object = json.loads(logged_info[0])

            assert (
                json_object[0]["topic"]
                == "org.fedoraproject.prod.git.receive.valgrind.master"
            )
            assert (
                json_object[1]["topic"]
                == "org.fedoraproject.prod.log.receive.valgrind.master"
            )
            assert len(json_object) == 2

    def test_dump_timespan(self):
        with patch("datanommer.commands.DumpCommand.get_config") as gc:
            self.config["before"] = "2013-02-16"
            self.config["since"] = "2013-02-14T08:00:00"
            gc.return_value = self.config

            time1 = datetime(2013, 2, 14)
            time2 = datetime(2013, 2, 15)
            time3 = datetime(2013, 2, 16, 8)

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                timestamp=time1,
                i=4,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                timestamp=time2,
                i=3,
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.log.receive.valgrind.master",
                timestamp=time3,
                i=2,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.DumpCommand()

            command.log.info = info
            with patch("datanommer.commands.datetime") as mock_dt:
                mock_dt.utcnow.return_value = datetime(2013, 3, 1)
                mock_dt.now.return_value = datetime(2013, 3, 1)
                command.run()

            json_object = json.loads(logged_info[0])

            assert (
                json_object[0]["topic"]
                == "org.fedoraproject.prod.git.receive.valgrind.master"
            )
            assert len(json_object) == 1

    def test_latest_overall(self):
        with patch("datanommer.commands.LatestCommand.get_config") as gc:
            self.config["overall"] = True
            gc.return_value = self.config

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.LatestCommand()

            command.log.info = info
            command.run()

            json_object = json.loads(logged_info[0])

            assert json_object[0]["git"]["msg"] == "Message 3"
            assert len(json_object) == 1

    def test_latest_topic(self):
        with patch("datanommer.commands.LatestCommand.get_config") as gc:
            self.config["topic"] = "org.fedoraproject.stg.fas.user.create"
            gc.return_value = self.config

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.LatestCommand()

            command.log.info = info
            command.run()

            json_object = json.loads(logged_info[0])

            assert json_object[0]["fas"]["msg"] == "Message 2"
            assert len(json_object) == 1

    def test_latest_category(self):
        with patch("datanommer.commands.LatestCommand.get_config") as gc:
            self.config["category"] = "fas"
            gc.return_value = self.config

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                category="git",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create",
                category="fas",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                category="git",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.LatestCommand()

            command.log.info = info
            command.run()

            json_object = json.loads(logged_info[0])

            assert json_object[0]["fas"]["msg"] == "Message 2"
            assert len(json_object) == 1

    def test_latest_timestamp_human(self):
        with patch("datanommer.commands.LatestCommand.get_config") as gc:
            self.config["overall"] = False
            self.config["timestamp"] = True
            self.config["human"] = True
            gc.return_value = self.config

            time1 = datetime(2013, 2, 14)
            time2 = datetime(2013, 2, 15, 15, 15, 15, 15)
            time3 = datetime(2013, 2, 16, 16, 16, 16, 16)

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                timestamp=time1,
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create", timestamp=time2, i=1
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                timestamp=time3,
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.LatestCommand()

            command.log.info = info
            with patch("datanommer.commands.datetime") as mock_dt:
                mock_dt.utcnow.return_value = datetime(2013, 3, 1)
                mock_dt.now.return_value = datetime(2013, 3, 1)
                command.run()

            json_object = json.loads(logged_info[0])

            assert json_object[1] == "2013-02-16 16:16:16.000016"
            assert json_object[0] == "2013-02-15 15:15:15.000015"
            assert len(json_object) == 2

    def test_latest_timestamp(self):
        with patch("datanommer.commands.LatestCommand.get_config") as gc:
            self.config["overall"] = False
            self.config["timestamp"] = True
            gc.return_value = self.config

            time1 = datetime(2013, 2, 14)
            time2 = datetime(2013, 2, 15)
            time3 = datetime(2013, 2, 16)

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                timestamp=time1,
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create", timestamp=time2, i=1
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                timestamp=time3,
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.LatestCommand()

            command.log.info = info
            with patch("datanommer.commands.datetime") as mock_dt:
                mock_dt.utcnow.return_value = datetime(2013, 3, 1)
                mock_dt.now.return_value = datetime(2013, 3, 1)
                command.run()

            json_object = json.loads(logged_info[0])

            assert json_object[1] == time.mktime(datetime(2013, 2, 16).timetuple())
            assert json_object[0] == time.mktime(datetime(2013, 2, 15).timetuple())
            assert len(json_object) == 2

    def test_latest_timesince(self):
        with patch("datanommer.commands.LatestCommand.get_config") as gc:
            self.config["overall"] = False
            self.config["timesince"] = True
            gc.return_value = self.config

            now = datetime(2013, 3, 1)
            time1 = now - timedelta(days=1)
            time2 = now - timedelta(seconds=60)
            time3 = now - timedelta(seconds=1)

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                timestamp=time1,
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create", timestamp=time2, i=1
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                timestamp=time3,
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.LatestCommand()

            command.log.info = info
            with patch("datanommer.commands.datetime") as mock_dt:
                mock_dt.utcnow.return_value = now
                mock_dt.now.return_value = now
                command.run()

            json_object = json.loads(logged_info[0])

            # allow .1 second to run test
            assert int(json_object[1]) <= 1.1
            assert int(json_object[1]) >= 1
            assert int(json_object[0]) <= 60.1
            assert int(json_object[0]) >= 60
            assert len(json_object) == 2

    def test_latest_timesince_human(self):
        with patch("datanommer.commands.LatestCommand.get_config") as gc:
            self.config["overall"] = False
            self.config["timesince"] = True
            self.config["human"] = True
            gc.return_value = self.config

            now = datetime.now()
            time1 = now - timedelta(days=2)
            time2 = now - timedelta(days=1)
            time3 = now - timedelta(seconds=1)

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                timestamp=time1,
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create", timestamp=time2, i=1
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                timestamp=time3,
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.LatestCommand()

            command.log.info = info
            command.run()

            json_object = json.loads(logged_info[0])

            # cannot assert exact value because of time to run test
            assert "day" not in json_object[1]
            assert "0:00:01." in json_object[1]
            assert "1 day in 0:00:00.", json_object[0]
            assert len(json_object) == 2

    def test_latest(self):
        with patch("datanommer.commands.LatestCommand.get_config") as gc:
            self.config["overall"] = False
            gc.return_value = self.config

            msg1 = m.Message(
                topic="org.fedoraproject.prod.git.branch.valgrind.master",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg2 = m.Message(
                topic="org.fedoraproject.stg.fas.user.create",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg3 = m.Message(
                topic="org.fedoraproject.prod.git.receive.valgrind.master",
                timestamp=datetime.utcnow(),
                i=1,
            )

            msg1.msg = "Message 1"
            msg2.msg = "Message 2"
            msg3.msg = "Message 3"

            m.session.add_all([msg1, msg2, msg3])
            m.session.flush()

            logged_info = []

            def info(data):
                logged_info.append(data)

            command = datanommer.commands.LatestCommand()

            command.log.info = info
            command.run()

            json_object = json.loads(logged_info[0])

            assert json_object[1]["git"]["msg"] == "Message 3"
            assert json_object[0]["fas"]["msg"] == "Message 2"
            assert len(json_object) == 2
