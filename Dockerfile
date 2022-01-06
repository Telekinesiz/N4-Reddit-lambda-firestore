FROM public.ecr.aws/lambda/python:3.8

# Copy function code
COPY main.py ${LAMBDA_TASK_ROOT}
COPY serviceAccountKey.json ${LAMBDA_TASK_ROOT}

# Avoid cache purge by adding requirements first
COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install --no-cache-dir -r requirements.txt

ARG praw_user_agent
ARG praw_client_id
ARG praw_client_secret
ARG praw_username

ENV praw_user_agent $praw_user_agent
ENV praw_client_id $praw_client_id
ENV praw_client_secret $praw_client_secret
ENV praw_username $praw_username

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "main.handler" ]