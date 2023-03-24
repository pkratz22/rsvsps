from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license_info = f.read()

setup(
    name='RS_vs_PS',
    version='0.1',
    description='Compare NBA player Regular Season vs Post-Season performance',
    long_description=readme,
    author='Peter Kratz',
    author_email='pkratz22@gmail.com',
    url='https://github.com/pkratz22/rsvsps',
    license=license_info,
    packages=find_packages(exclude=('tests', 'docs'))
)
