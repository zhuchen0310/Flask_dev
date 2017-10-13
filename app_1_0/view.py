# coding = utf-8

from flask import Flask, render_template, url_for

from . import api

@api.route('/users')
def user_info():
    return u'客户中心'

@api.route('/goods')
def good_info():
    return u'商品中心'