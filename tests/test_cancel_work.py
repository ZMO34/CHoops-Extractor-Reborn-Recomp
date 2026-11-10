from choops_recomp.ui.app import Work


def test_cancelled_worker_does_not_publish_partial_result(qapp):
    work=Work(lambda progress:(progress(0,10,'index'),42)[1]);events=[];work.signals.result.connect(lambda result:events.append('result'));work.signals.cancelled.connect(lambda:events.append('cancelled'));work.cancelled=True;work.run();assert events==['cancelled']
