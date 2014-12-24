from daisychain.steps.marker import Marker

def test_marker():
    s = Marker(name='marker_step')
    assert s.status.pending
    assert s.name == 'marker_step'
    s.run()
    assert s.status.finished
