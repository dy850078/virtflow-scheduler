rabbitmq-up:
	docker run -d --hostname rabbitmq \
		--name rabbitmq \
		-p 5672:5672 \
		-p 15672:15672 \
		-e RABBITMQ_DEFAULT_USER=guest \
		-e RABBITMQ_DEFAULT_PASS=guest \
		rabbitmq:3-management

rabbitmq-down:
	docker stop rabbitmq && docker rm rabbitmq

worker-up:
	python3 -m app.core.rmq_worker

node-up:
	uvicorn app.api.node-endpoints:app --host 0.0.0.0 --port 5000 --reload

scheduler-up:
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
	