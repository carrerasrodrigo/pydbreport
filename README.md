PyDbReport
==========

PyDbReport is a light report system that sends information by email, following these steps:

1. Run a specified query into a MySql db. 
2. Render the query into a html table or a csv file.
3. Send the rendered information by email. 

Every report that we want to send can contain as many queries as we want. The queries are specified by 
an xml file. 


How to install it?
-----------------------
You can install it with pip doing the following:
    
    $ pip install -e git+https://github.com/carrerasrodrigo/pydbreport.git#egg=pydbreport
    
or you can clone this repository and install it. 

    $ git clone https://github.com/carrerasrodrigo/pydbreport.git
    $ cd pydbreport
    $ python setup.py install
    
    
How to create a report?
-----------------------

### Report Sintax

First we need to create an xml file that will contain the queries with the information
that you want to send. The format of the xml it's the following:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<job>
    <emails>
        <email>email1@t.com</email>
        <email>email2@t.com</email>
        <cc>cc@cc.com</cc>
        <bcc>bcc@bcc.com</bcc>
    </emails>
    <subject>test report</subject>
    <sender>sender@email.com</sender>
    <day>*</day>
    <queries>
        <query>
            <db_name>pydbreport</db_name>
            <db_user>root</db_user>
            <db_password>admin</db_password>
            <db_host>localhost</db_host>
            <transpose>0</transpose>
            <csv>1</csv>
            <csv_name>test.csv</csv_name>
            <code>
                <![CDATA[
                    select first_name, rating from famous_people where age < 70; 
                ]]>
            </code>
        </query>
    </queries>
</job>
```
 - Into the tag **emails** we specify all the recipients that will receive the email. Note that you can use *email*, *cc* or *bcc* depending with kind of sender do you wanna use.
 - **subject** represents the subject of the email 
 - **sender** an email that represents the sender of the report
 - **weekday** will specify a list of days on witch the report it's gonna be executed. 
 You can use '*' to execute the report every day or '0,1' to send 
 the email on mondays and tuesdays.
- **day** you need to write a number between 1-31 that will represent the day
of the month on witch the report will be excuted. If the tag **day** and **weekday** are
    added at the same time, **weekday** will be ignored. 
- **queries** is a list of **query** that will be attached to the email. 
- **query** is a query that will be attached to the email with the following tags
    **db_name** represents the name of the database where we want to connect
    **db_user** represents the name of the user that it's gonna be used to connect to the database.
    **db_password** represents the password of the user that it's gonna be used to connect to the database.
    **db_host** The host where the database is running. 
    **transpose** Tells if the table generated after the query has to be transposed. O means False, 1 means True.
    **csv** Tells if the table should be attached to a csv file or rendered in the body of the email. O means False, 1 means True.
    **csv_name** The name of the csv attached. If **cvs** is 0, it will be ignored. 
    **code** The SQL that will be run into the database. It's recommended to write this code into
        a CDATA tag.
    **template_path** This tag represents the absolute path of the template we want to use to render our query. If we
        miss this tag *PyDbReport* it's going to use a default template.



### Report execution

Once we have created the reports we need to run the **pydbr** in order to execute them, 
here you have some examples:

    $ pydbr --xml myreport.xml
    $ pydbr --xml --reportpath /my/reports/path/


**pydbr** has the following arguments:

- **output**: email or screen. If it's email, it will send the report by email otherwise, it will print it on the screen
- **emails**: Ignores the list of emails added in the xml file and sends to the indicated emails. Ex: ema1@compar.com|em@asd.com
- **xml**: The path of the xml that you want to use. If it's not used, the script will read all the *.xml from the works folder
- **reportpath**: The path where we want to scan all our reports. It's ignored if the --xml argument it's present. 
- **smtp-host**: The SMTP host
- **smtp-port**: The SMTP host port
- **csv-tmp-folder**: The folder where the csv files will be saved temporarily


### How to run the reports every day?

If you are looking forward into running reports every day you can add **pydbr** into a cronjob in order to run it, you can add 
the following code to your crontab:
    
    0 * * * * pydbr --xml myreport.xml


### Personalize your emails, Template System

PyDbReport uses jinja2 in order to render the templates, by default it ships with basic template
to render the tables but you can define yours using jinja sintaxs. For example:

```html
{# My template #}
<p>This is my awesome template</p>
<table>
    {% for row in table %}
        <tr>
            {% for cell in row %}
                <td>
                    {{ cell }}
                </td>
            {% endfor %}
        </tr>
    {% endfor %}
</table>
```

Then you need to specify to *pydbr* which template you want to use for your query.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<job>
   ...
    <queries>
        <query>
            ...
            <template_path>/absolute_path/to/my/template.jinja</template_path>
            <code>
                <![CDATA[
                    select first_name, rating from famous_people where age < 70; 
                ]]>
            </code>
        </query>
    </queries>
</job>
```

### Tested

This project has been tested on Python 2.6.7+, Python 2.7+ and Python 3.3+
