from setuptools import find_packages, setup

setup(
    name="flask-youtubedl",
    author="/etc/sudonters",
    author_email="etcsudonters@gmail.com",
    version="0.0.1",
    packages=find_packages("src", exclude=[]),
    package_dir={"": "src"},
    description="Marrying flask and youtube-dl",
    install_requires=[
        "flask>=1.1.2<2.0.0",
        "youtube-dl>=2021.1.24.1",
        "celery>=5.0.0<6.0.0",
        "redis>=3.5.3<4.0.0",
        "flask-wtf>=0.14.3,<1.0.0",
        "flask-sqlalchemy>=2.4.4,<3.0.0",
        "marshmallow-annotations",
    ],
    license="MIT",
    zip_safe=False,
    entry_points="""
        [console_scripts]
        fytdl=flask_youtubedl.cli:fytdl
"""
)
