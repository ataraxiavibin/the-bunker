# run.sh
#
# just auto-reload script when it changes

uvicorn bunker:app --host 0.0.0.0 --port 5050 --reload
