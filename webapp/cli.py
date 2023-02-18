from webapp import webapp
import click
import os

@webapp.cli.group()
def foo():
    """Silly test commands."""
    print('foo: getting ready')
    pass

@foo.command()
def woot():
    """celebrate."""
    print('Woot!!')

@foo.command()
def bar():
    """Print foobar"""
    print('Foobar!! Yowza!' )
