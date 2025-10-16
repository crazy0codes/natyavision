#!/bin/bash
set - e

cd backend

source venv/bin/activate

uvicorn main:app --reload
