import os
import pathlib

import jinja2
from flask import Flask, session, redirect, request
from sqlmodel import select

from src.core.container import Container
from src.core.exceptions import ValidationError, AuthError
from src.model.models import ClassificationModelORM
from src.schema.auth_schema import SignIn
from src.schema.user_schema import User

app = Flask(__name__)
app.secret_key = 'VSLLJGISDHGJKZNCVJKV'
template_path_dir = pathlib.Path(__file__).parent / 'templates'
jinja_env = jinja2.Environment(
   loader=jinja2.FileSystemLoader(str(template_path_dir)),
)


auth_service = Container().auth_service()
user_service = Container().user_service()
database = Container().db()
dashboard_fqdn = os.getenv("DASHBOARD_APP_URL")


def get_user_from_session():
    user_data = session.get('user')
    if not user_data:
        return None
    user = User.model_validate(user_data)
    return user


@app.get('/')
def get_nav_page():
    template = jinja_env.get_template('nav_template.html')
    user = get_user_from_session()
    if not user:
        return redirect('/login')
    model_query = select(ClassificationModelORM)
    with database.session() as db_ses:
        models = db_ses.execute(model_query).scalars().all()
    return template.render(**dict(
        user=user,
        models=models,
        dash_site=dashboard_fqdn
    ))


@app.get('/balance/increase/')
def increase_balance():
    user = get_user_from_session()
    if not user:
        return redirect('/login')
    user = user_service.patch_attr(user.id, 'balance', user.balance + 500)
    session.update(user=user.model_dump())
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        try:
            signin_info = SignIn(**request.form)
            user_data = auth_service.sign_in(signin_info)
        except ValidationError:
            return redirect('/login')
        except AuthError:
            return redirect('/login')
        session['user'] = user_data['user_info'].model_dump()
        return redirect('/')
    else:
        template = jinja_env.get_template('login.html')
        return template.render()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)
