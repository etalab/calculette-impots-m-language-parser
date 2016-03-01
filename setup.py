#! /usr/bin/env python3
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


setup(
    name='m_language_parser',
    version='0.0.0.dev0',

    author='Christophe Benz',
    author_email='christophe.benz@data.gouv.fr',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        # 'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Information Analysis',
        ],
    description='M language parser',
    keywords='calculateur impôts tax',
    # license='http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    # url='',

    install_requires=['Arpeggio', 'toolz'],
    packages=find_packages(),
    )
