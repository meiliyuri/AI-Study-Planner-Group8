## Title pages and page id ##
It is possible to change the title of the current page and id by using the blocks
```
<title>{% block title %}- <YOUR_TITLE>{% endblock %}</title>
```
```
  {% block classbody %}
  <body id="YOUR_ID">
  {% endblock %}
```
<BR>

## To reset (nuke) DB to start again: ##

Do this instead of DB migrations, no need in a project this size.

- Delete migrations dir & all sub-dirs
- Delete app.db
- Run at a 2nd venv prompt:
```
flask db init
flask db migrate
flask db upgrade
```