from daisychain.steps.input import InMemoryInput
from daisychain.instantiator import Instantiator, ANONYMOUS_SUFFIX
from daisychain.steps.wait import Wait
from daisychain.steps.system.run_command import RunCommand
from daisychain.steps.authentication.basic_auth import BasicAuth
from daisychain.steps.marker import Marker
from daisychain.reference import CircularReferenceError

config = {
    "step1":{
        "class": "daisychain.**.BasicAuth",
        "username": "mockusername",
        "password": "mockpassword"
        },
    "step2":{
        "class": "daisychain.steps.wait.Wait",
        "seconds": 0.1
        },
    "step3":{
        "class": "daisychain.**.RunCommand",
        "command": "ls -l",
        "authentication": "step1",
        "dependencies": [ "step2" ]
        }
    }

def test_simple_success():
    step = Instantiator(config=config)
    step.root_log_id = 'instantiator'
    step.run()
    step1 = step.steps['step1']
    step2 = step.steps['step2']
    step3 = step.steps['step3']

    assert isinstance(step1, BasicAuth)
    assert isinstance(step2, Wait)
    assert isinstance(step3, RunCommand)
    assert step3.authentication is step1
    assert step3.dependencies == {step2}

def test_step_with_no_class_failure():
    step = Instantiator(config={'step1':{'not_the_class_key':'notamodule.NotAClass'}})
    try:
        step.run()
    except KeyError:
        pass
    else:
        assert False, "Should have raised a KeyError on class not found"

def test_cannot_find_class_failure():
    step = Instantiator(config={'step1':{'class':'notamodule.NotAClass'}})
    try:
        step.run()
    except KeyError:
        pass
    else:
        assert False, "Should have raised a KeyError on class not found"

def test_cannot_find_step_failure():
    step = Instantiator(config={'step1':{'class':'daisychain.**.Marker', 'dependencies': ['notastep']}})
    try:
        step.run()
    except KeyError:
        pass
    else:
        assert False, "Should have raised a KeyError on class not found"

    step = Instantiator(config={'step1':{'class':'daisychain.**.RunCommand', 'command': 'ls -1', 'authentication': 'notastep'}})
    try:
        step.run()
    except KeyError:
        pass
    else:
        assert False, "Should have raised a KeyError on class not found"

def test_step_circular_dependencies():
    step = Instantiator(config={'step1':{'class':'daisychain.**.Marker', 'dependencies': ['step2']},'step2':{'class':'daisychain.**.Marker', 'dependencies': ['step1']}})
    try:
        step.run()
    except CircularReferenceError:
        pass
    else:
        assert False, "Should have raised a CircularReferenceError"

def test_anonymous_reference():
    step = Instantiator(config={
        'run':{
            'class': 'daisychain.**.RunCommand',
            'command': 'sudo ls -l',
            'authentication': {
                'class': 'daisychain.**.BasicAuth',
                'username': 'mockuser',
                'password': 'mockpassword',
                'dependencies': [
                    {'class':'daisychain.**.Marker'},
                    'run_dep'
                    ]
                },
            'dependencies': [
                {'class':'daisychain.**.Marker'},
                'run_dep'
                ]
            },
        'run_dep':{
            'class': 'daisychain.**.Marker'
            }
        })
    step.run()
    run_step = step.steps['run']
    auth_step = step.steps['run.authentication.' + ANONYMOUS_SUFFIX]
    auth_dep_inline = step.steps['run.authentication.' + ANONYMOUS_SUFFIX + '.dependencies.0.' + ANONYMOUS_SUFFIX]
    run_dep_inline = step.steps['run.dependencies.0.' + ANONYMOUS_SUFFIX]
    dep_named = step.steps['run_dep']

    assert isinstance(auth_step, BasicAuth)
    assert isinstance(run_step, RunCommand)
    assert run_step.authentication is auth_step
    assert run_step.dependencies == {run_dep_inline, dep_named}
    assert auth_step.username == 'mockuser'
    assert auth_step.password == 'mockpassword'
    assert auth_step.dependencies == {auth_dep_inline, dep_named}
    assert run_dep_inline.name == 'run.dependencies.0.' + ANONYMOUS_SUFFIX
    assert auth_dep_inline.name == 'run.authentication.' + ANONYMOUS_SUFFIX + '.dependencies.0.' + ANONYMOUS_SUFFIX

def test_anonymous_reference_name_collision():
    step = Instantiator(config={'run':{'class':'daisychain.**.RunCommand', 'command': 'sudo ls -l', 'authentication': {'class': 'daisychain.**.BasicAuth', 'username': 'mockuser', 'password': 'mockpassword'}, 'dependencies': [{'class':'daisychain.**.Marker'}]}, 'run.authentication.' + ANONYMOUS_SUFFIX: {'class': 'daisychain.**.Marker'}})
    try:
        step.run()
    except KeyError:
        pass
    else:
        assert False, "Should have raised a KeyError when an anonymous reference has the same name as an existing step"
