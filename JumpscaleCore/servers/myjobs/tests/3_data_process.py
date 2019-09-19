import gevent
from Jumpscale import j


def main(self, count=20):
    """
    kosmos -p 'j.servers.myjobs.test("data_process")'
    """
    self.stop(reset=True)

    def wait_1sec():
        gevent.sleep(1)
        return "OK"

    job_sch = j.servers.myjobs.schedule(wait_1sec)
    # just to have 1

    len(j.servers.myjobs.find()) == 1

    # lets now delete and check the index is empty
    j.servers.myjobs.delete()
    # we also need to clear the internal scheduled_ids
    j.servers.myjobs.scheduled_ids = []

    # get the sqlite peewee model we can work with to query
    Jobs = j.servers.myjobs.jobs._model.index.sql

    # should be zero because we emptied the table
    assert len([(item.id) for item in Jobs.select()]) == 0

    ids = []
    for x in range(count):
        job_sch = j.servers.myjobs.schedule(wait_1sec)
        ids.append(job_sch.id)

    r = [(item.id) for item in Jobs.select().where(Jobs.state == "NEW")]
    assert len(r) == count

    # default autosave is on and needs to be one
    assert job_sch._data._autosave == True

    job_sch.state = "RUNNING"

    assert job_sch.load().state == "RUNNING"
    assert job_sch.state == "RUNNING"

    r = [(item.id, item.state) for item in Jobs.select().where((Jobs.state == "RUNNING") | (Jobs.state == "NEW"))]
    assert len(r) == count
    r = [(item.id, item.state) for item in Jobs.select().where(Jobs.state == "NEW")]
    assert len(r) == count - 1

    # change it back and is also test for autosave
    job_sch.state = "NEW"
    assert job_sch._data._autosave == True
    r = [(item.id, item.state) for item in Jobs.select().where(Jobs.state == "NEW")]
    assert len(r) == count

    self.workers_tmux_start(4)

    print(ids)
    jobs = self.wait(ids)
    self.stop()
    for job in jobs:
        assert job.result == "OK"

    print("TEST OK")
