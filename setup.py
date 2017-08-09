from distutils.core import setup
setup(
    name = 'blockaudio',
    version = '0.1',
    package_dir = {'blockaudio': 'src'},
    packages = ['blockaudio',
                'blockaudio.commons',
                'blockaudio.formulators',
                'blockaudio.editors',
                'blockaudio.audio_blocks',
                'blockaudio.audio_boxes'],
    package_data = {}
)
