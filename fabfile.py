from os.path import join
from fabric.api import run, env, local, sudo, put, require, cd
from fabric.contrib.project import rsync_project
from fabric import utils
from fabric.contrib import console

RSYNC_EXCLUDE = (
    '.bzr',
    '.bzrignore',
    '.git',
    '.gitignore',
    '*.pyc',
    '*.example',
    '*.db',
    'media',
    'local_settings.py',
    'fabfile.py',
    'bootstrap.py',
    'tags',
    'PYSMELL*'
)

env.project = 'lutrisweb'


def _setup_path():
    env.root = join(env.home, env.domain)
    env.code_root = join(env.root, env.project)


def staging():
    """ use staging environment on remote host"""
    env.home = '/srv/django'
    env.user = 'django'
    env.environment = 'staging'
    env.domain = 'dev.lutris.net'
    env.hosts = [env.domain]
    _setup_path()


def production():
    """ use production environment on remote host"""
    env.home = '/srv/django'
    env.user = 'django'
    env.environment = 'production'
    env.domain = 'lutris.net'
    env.hosts = [env.domain]
    _setup_path()


def touch():
    """Touch wsgi file to trigger reload."""
    require('code_root', provided_by=('staging', 'production'))
    conf_dir = join(env.code_root, 'config')
    with cd(conf_dir):
        run('touch %s.wsgi' % env.project)


def apache_reload():
    """ reload Apache on remote host """
    sudo('service apache2 reload', shell=False)


def test():
    local("python manage.py test games")
    local("python manage.py test accounts")


def initial_setup():
    """Setup virtualenv"""
    run("mkdir -p %s" % env.root)
    with cd(env.root):
        run('virtualenv --no-site-packages .')


def bootstrap():
    put('requirements.txt', env.root)
    with cd(env.root):
        run('source ./bin/activate && '
            'pip install --requirement requirements.txt')


def update_vhost():
    local('cp config/%(project)s.conf /tmp' % env)
    local('sed -i s#%%ROOT%%#%(root)s#g /tmp/%(project)s.conf' % env)
    local('sed -i s/%%PROJECT%%/%(project)s/g /tmp/%(project)s.conf' % env)
    local('sed -i s/%%ENV%%/%(environment)s/g /tmp/%(project)s.conf' % env)
    local('sed -i s/%%DOMAIN%%/%(domain)s/g /tmp/%(project)s.conf' % env)
    put('/tmp/%(project)s.conf' % env, '%(root)s' % env)
    sudo('cp %(root)s/%(project)s.conf ' % env +
         '/etc/apache2/sites-available/%(domain)s' % env, shell=False)
    sudo('a2ensite %(domain)s' % env, shell=False)


def rsync():
    """ rsync code to remote host """
    require('root', provided_by=('staging', 'production'))
    if env.environment == 'production':
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    extra_opts = '--omit-dir-times'
    rsync_project(
        env.root,
        exclude=RSYNC_EXCLUDE,
        delete=True,
        extra_opts=extra_opts,
    )


def copy_local_settings():
    require('code_root', provided_by=('staging', 'production'))
    put('config/local_settings_%(environment)s.py' % env, env.code_root)
    with cd(env.code_root):
        run('mv local_settings_%(environment)s.py local_settings.py' % env)


def migrate():
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.code_root):
        run("source ../bin/activate; "
            "python manage.py migrate --no-initial-data")


def syncdb():
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.code_root):
        run("source ../bin/activate; "
            "python manage.py syncdb --noinput")


def collect_static():
    require('code_root', provided_by=('stating', 'production'))
    with cd(env.code_root):
        run('source ../bin/activate; python manage.py collectstatic --noinput')


def configtest():
    sudo("apache2ctl configtest")


def deploy():
    rsync()
    copy_local_settings()
    bootstrap()
    collect_static()
    syncdb()
    migrate()
    update_vhost()
    configtest()
    apache_reload()