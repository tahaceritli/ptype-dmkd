import setuptools

with open("README.md", "r") as fh:
   long_description = fh.read()

setuptools.setup(
   name='ptype',
   version='1.0',
   description='Probabilistic type inference',
   long_description=long_description,
   long_description_content_type="text/markdown",
   author='Taha Ceritli, Christopher K. I. Williams, James Geddes',
   author_email='t.y.ceritli@sms.ed.ac.uk, ckiw@inf.ed.ac.uk, jgeddes@turing.ac.uk',
   url='https://github.com/alan-turing-institute/ptype-dmkd',
   packages=setuptools.find_packages(),
   classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
   ],
   install_requires=['numpy', 'scipy', 'scikit-learn', 'matplotlib', 'pandas', 'greenery', 'clevercsv']
)