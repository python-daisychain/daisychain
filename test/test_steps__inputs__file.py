from daisychain.steps.inputs.file import InputFile

TEST_STRING = 'THIS STRING IS COMPLETELY UNIQUE AND WILL NOT EXIST EVER AGAIN'

def test_input_file():
    i = InputFile(path=__file__)
    assert i.pending
    i.run()
    assert i.finished
    assert TEST_STRING in i.output
