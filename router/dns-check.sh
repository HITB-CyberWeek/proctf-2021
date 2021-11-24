#!/bin/bash
while true; do echo `date; timeout 1 host ya.ru | grep address`; sleep 5; done
