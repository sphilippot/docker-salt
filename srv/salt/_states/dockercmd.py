import salt.utils
from salt.exceptions import CommandExecutionError

def __virtual__():
    '''
    Only load if docker exists on the system
    '''
    if salt.utils.which('docker'):
        return 'dockercmd'
    return False

retPrototype = {
    'name':None,
    'changes':{},
    'result':None,
    'comment':None
}

def running(name,
            image,
            ports=None,
            volumes=None,
            reload=False,
            **kwargs):
    ret = retPrototype.copy()
    ret['name'] = name

    #kill existing container
    inspect = __salt__['dockercmd.inspect'](name)
    is_running = inspect['State']['Running']
    if is_running and not reload:
        ret['result'] = True
        ret['comment'] = '"%s" is already running.' % (name)
        return ret
    else:
        #upper case ID is for running container
        id = inspect['ID']
        __salt__['dockercmd.kill'](name)
        __salt__['dockercmd.rm'](name)
        ret['comment'] = 'killed and removed id ' + id

    try:
        result = __salt__['dockercmd.run'](name, image, ports, volumes, reload)
        ret['result'] = True
        if isinstance(result, dict):
            ret['changes'] = result
        else:
            ret['comment'] = result
    except CommandExecutionError as ex:
        ret['result'] = False
        ret['comment'] = str(ex)
    return ret

def built(name,
          dockerfile,
          nocache=False,
          force=False,
          **kwargs):
    ret = retPrototype.copy()
    ret['name'] = name

    #check if already built
    inspect = __salt__['dockercmd.inspect'](name)
    if inspect['id'] and not force:
        ret['result'] = True
        ret['comment'] = '"%s" already exist with id="%s".' % (name, inspect['id'])
        return ret

    result = __salt__['dockercmd.build'](name, dockerfile, nocache)
    if 'Successfully built' in result['stdout']:
        inspect = __salt__['dockercmd.inspect'](name)
        ret['result'] = True
        ret['changes'] = inspect
    else:
        ret['result'] = False
        ret['comment'] = result
    return ret

def mod_watch(name, **kwargs):
    if kwargs['sfun'] == 'running':
        if kwargs.get('reload'):
            kwargs.pop('reload')
        return running(name, reload=True, **kwargs)
    elif kwargs['sfun'] == 'built':
        if kwargs.get('force'):
            kwargs.pop('force')
        return built(name, force=True, **kwargs)
