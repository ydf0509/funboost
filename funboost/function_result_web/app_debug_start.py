from funboost.function_result_web.app import app


if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=27019)

