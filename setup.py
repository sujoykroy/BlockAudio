from distutils.core import setup
setup(
    name = 'dawpy',
    version = '0.1',
    package_dir = {'dawpy': 'src'},
    packages = ['dawpy',
                'dawpy.commons',
                'dawpy.formulators',
                'dawpy.editors',
                'dawpy.audio_blocks',
                'dawpy.audio_boxes'],
    package_data = {}
)
