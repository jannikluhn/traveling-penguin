import datetime
import logging
import json
import os
import lb_tracking_api

# import boto3
# import botocore.exceptions

USERNAME = os.getenv("LIGHTBUG_USERNAME")
PASSWORD = os.getenv("LIGHTBUG_PASSWORD")
DEVICE_ID = float(os.getenv("LIGHTBUG_DEVICE_ID"))
BUCKET_NAME = os.getenv("BUCKET_NAME")
POINTS_KEY = os.getenv("POINTS_KEY")
POINTS_PER_QUERY = int(os.getenv("POINTS_PER_QUERY"))
CUTOFF_TIMESTAMP = os.getenv("CUTOFF_TIMESTAMP")

logging.getLogger().setLevel(logging.DEBUG)

# s3 = boto3.client("s3")


def load_points():
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=POINTS_KEY)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            points = []
        else:
            raise
    else:
        points = json.load(response["Body"])
    logging.info(f"loaded {len(points)} points")
    return points


def save_points(points):
    logging.info(f"saving {len(points)} points")
    s = json.dumps(points, indent=4, sort_keys=True, default=str)
    s3.put_object(Bucket=BUCKET_NAME, Key=POINTS_KEY, Body=s)


def fetch_points(prev_point):
    client = lb_tracking_api.ApiClient()
    user_api = lb_tracking_api.UserApi(client)

    token = user_api.user_login({"username": USERNAME, "password": PASSWORD})
    user_id = token.user_id
    client.set_default_header(header_name="Authorization", header_value=token.id)
    device_api = lb_tracking_api.DeviceApi(client)

    if prev_point:
        prev_timestamp_str = prev_point["timestamp"]
    else:
        prev_timestamp_str = CUTOFF_TIMESTAMP
    prev_timestamp = datetime.datetime.fromisoformat(prev_timestamp_str)

    logging.info("fetching new points")
    all_points = []
    while True:
        timestamp_gt = prev_timestamp + datetime.timedelta(seconds=1)
        timestamp_gt_str = timestamp_gt.strftime("%Y-%m-%d %H:%M:%S")
        logging.debug(
            f"fetched {len(all_points)} so far, requesting from timestamp {timestamp_gt_str}"
        )
        f = {
            "limit": POINTS_PER_QUERY,
            "order": "timestamp ASC",
            "where": {"timestamp": {"gt": timestamp_gt_str}},
        }
        point_objs = device_api.device_prototype_get_points(
            DEVICE_ID,
            filter=json.dumps(f),
        )
        points = [p.to_dict() for p in point_objs]
        if points and all_points:
            if points[0]["timestamp"] <= all_points[-1]["timestamp"]:
                raise ValueError(
                    f"failed to make progress making requests: prev {all_points[-1]}, next {points[0]}"
                )
        all_points.extend(points)

        if len(points) < POINTS_PER_QUERY:
            break
        prev_timestamp = points[-1]["timestamp"]

    if all_points:
        last_timestamp = all_points[-1]["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_timestamp = "?"
    logging.info(f"fetched {len(all_points)} points up to timestamp {last_timestamp}")
    return all_points


def main():
    # prev_points = load_points()
    prev_points = []
    if len(prev_points) > 0:
        last_point = prev_points[-1]
    else:
        last_point = None
    new_points = fetch_points(last_point)
    all_points = prev_points + new_points
    # save_points(all_points)


def lambda_handler(event, context):
    main()


if __name__ == "__main__":
    main()
