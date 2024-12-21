"""
Medical Research Platform Backend
-------------------------------
Package configuration for the Medical Research Platform backend services.
Defines core dependencies, development tools, and package metadata.

Dependencies are strictly versioned to ensure reproducible builds while
allowing compatible updates through version constraints.
"""

import os
from setuptools import setup, find_packages  # version 68.0.*

def read_requirements():
    """
    Read and validate package dependencies from requirements.txt file.
    
    Returns:
        list: List of validated package requirements strings
    
    Raises:
        FileNotFoundError: If requirements.txt is missing
        ValueError: If requirement format is invalid
    """
    requirements = []
    try:
        req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
        return requirements
    except FileNotFoundError:
        # Fall back to core dependencies defined below if file not found
        return []

# Package metadata
PACKAGE_NAME = "medical-research-platform"
VERSION = "0.1.0"
DESCRIPTION = "Backend services for the Medical Research Platform enabling secure, scalable community-driven medical research"
AUTHOR = "Medical Research Platform Team"
LICENSE = "MIT"
PYTHON_REQUIRES = ">=3.11"

# Core dependencies with strict version constraints
INSTALL_REQUIRES = [
    # Web Framework
    'django>=4.2.0,<5.0.0',
    'django-ninja>=0.22.0,<0.23.0',
    'gunicorn>=21.2.0,<22.0.0',
    
    # Task Queue
    'celery>=5.3.0,<6.0.0',
    
    # Data Processing
    'numpy>=1.24.0,<2.0.0',
    'pandas>=2.0.0,<3.0.0',
    'scipy>=1.11.0,<2.0.0',
    
    # Database
    'psycopg2-binary>=2.9.0,<3.0.0',
    
    # Caching & Messaging
    'redis>=4.6.0,<5.0.0',
    'pika>=1.3.0,<2.0.0',
    
    # AWS Integration
    'boto3>=1.28.0,<2.0.0',
    
    # Security
    'pyjwt>=2.7.0,<3.0.0',
    'cryptography>=41.0.0,<42.0.0',
    
    # HTTP & Environment
    'requests>=2.31.0,<3.0.0',
    'python-dotenv>=1.0.0,<2.0.0',
]

# Development dependencies
DEV_REQUIRES = [
    # Testing
    'pytest>=7.4.0,<8.0.0',
    'pytest-cov>=4.1.0,<5.0.0',
    'pytest-django>=4.5.0,<5.0.0',
    
    # Type Checking
    'mypy>=1.4.0,<2.0.0',
    'django-stubs>=4.2.0,<5.0.0',
    
    # Code Quality
    'black>=23.7.0,<24.0.0',
    'flake8>=6.1.0,<7.0.0',
    'isort>=5.12.0,<6.0.0',
    
    # Security
    'bandit>=1.7.0,<2.0.0',
    'safety>=2.3.0,<3.0.0',
]

setup(
    # Package Metadata
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    license=LICENSE,
    python_requires=PYTHON_REQUIRES,
    
    # Package Configuration
    packages=find_packages(exclude=['tests*', 'docs*']),
    include_package_data=True,
    
    # Dependencies
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'dev': DEV_REQUIRES,
    },
    
    # PyPI Classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Healthcare Industry',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Security :: Cryptography',
        'Operating System :: OS Independent',
    ],
    
    # Project URLs
    project_urls={
        'Source': 'https://github.com/medical-research-platform/backend',
        'Documentation': 'https://docs.medical-research-platform.org',
    },
)