from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

scrapy_path = '/usr/src/scrapy'

default_args = {
    'owner': 'Greener',
    'description': 'Fluxo de automação para os Crawlers',
    'start_date': datetime(2023, 8, 27),
    'schedule_interval': '@daily',
    'retries': 3,
    'retry_delay': timedelta(minutes = 3)
}

with DAG(
    'scrapy_crawlers',
    default_args = default_args,
    template_searchpath = scrapy_path
) as dag:

    scrapy_solplace = BashOperator(
        task_id = 'scrapy_crawler_solplace',
        bash_command = f'cd {scrapy_path} && scrapy crawl solplace',
        dag = dag
    )

    scrapy_solplace = BashOperator(
        task_id = 'scrapy_crawler_aldo',
        bash_command = f'cd {scrapy_path} && scrapy crawl aldo',
        dag = dag
    )
