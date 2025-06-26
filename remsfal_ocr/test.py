# Datei zum Testen der Kafka Konfiguration

import json
import time
from kafka import KafkaProducer, KafkaConsumer

topic = 'ocr.documents.to_process'
bootstrap_servers = 'localhost:9092'
group_id = 'test-group'

message = {
    "bucket": "remsfal-chat-files",
    "fileName": "test-image.png",
    "sessionId": "123",
    "messageId": "123",
}

testConsumer = False

producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
)
print(f"[Producer] Sende Nachricht an Topic '{topic}': {message}")
producer.send(topic, message)
producer.flush()
print("[Producer] Nachricht wurde gesendet.\n")

if testConsumer:
    # Warten auf Kafka-Verarbeitung
    time.sleep(1)

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset='earliest',
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    )

    print("[Consumer] Warte auf Nachricht...")
    for msg in consumer:
        print(f"[Consumer] Empfangen: {msg.value}")
        break 

    consumer.close()
    print("[Consumer] Fertig.")
