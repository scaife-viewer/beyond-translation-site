#!/bin/bash
isort -rc scaife_stack_atlas
black scaife_stack_atlas
flake8 scaife_stack_atlas
