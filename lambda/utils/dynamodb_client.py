from boto3.dynamodb.conditions import Key
from datetime import datetime

def get_last_report_info(table, domain):
    response = table.query(
        KeyConditionExpression=Key('domain').eq(domain),
        ScanIndexForward=False,
        Limit=1
    )
    items = response.get('Items', [])
    if items:
        last_item = items[0]
        timestamp = datetime.fromisoformat(last_item['timestamp'])
        emails = last_item.get('emails_sent', [])
        return {"timestamp": timestamp, "emails": emails}
    return None
