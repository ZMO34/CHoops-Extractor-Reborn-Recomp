from choops_recomp.ui.app import Studio


def test_audio_categories_are_separate(qtbot):
    window=Studio(offscreen=True);qtbot.addWidget(window)
    assert [window.tabs.tabText(i) for i in range(window.tabs.count())]==['Models / Courts','Textures','Audio','Roster','Mods / Mod Projects']
    assert [window.audio_categories.tabText(i) for i in range(window.audio_categories.count())]==['Licensed Music','Band / Fight Songs','Other Audio']


def test_failed_result_callback_releases_worker(qtbot):
    window=Studio(offscreen=True);qtbot.addWidget(window)
    def fail(value):raise ValueError('test callback failure')
    window.run_job(lambda progress:1,fail)
    qtbot.waitUntil(lambda:not window.jobs)
    assert window.last_error=='test callback failure'
