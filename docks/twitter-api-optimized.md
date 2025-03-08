# Twitter API Reference

## 1. Overview

A high-performance third-party Twitter API with reliable stability, high QPS support, and cost-effective pricing.

- **Stability:** Handles over 1,000,000 API calls
- **Performance:** Average response time of 700ms
- **QPS Support:** Up to 200 QPS per client
- **Design:** RESTful API using standard OpenAPI specifications
- **Pricing:**
  - $0.15 per 1,000 tweets
  - $0.18 per 1,000 user profiles
  - $0.15 per 1,000 followers
  - Minimum charge: $0.00015 per request

## 2. Authentication

All API requests require authentication using an API key in the HTTP headers.

```
X-API-Key: your_api_key_here
```

## 3. User Endpoints

### 3.1 Get User Info by Username

**Endpoint:** `GET /twitter/user/info`

**Parameters:**
- `userName` (string, required): Twitter username

**Response:** User profile containing:
- id, userName, url, name, isBlueVerified, profilePicture, coverPicture
- description, location, followers, following, canDm
- createdAt, fastFollowersCount, favouritesCount, hasCustomTimelines
- isTranslator, mediaCount, statusesCount, withheldInCountries
- possiblySensitive, pinnedTweetIds, isAutomated, automatedBy

### 3.2 Batch Get User Info By UserIds

**Endpoint:** `GET /twitter/user/batch_info_by_ids`

**Parameters:**
- `userIds` (string, required): Comma-separated list of user IDs

**Pricing:**
- Single user: 18 credits per user
- Bulk request (100+ users): 10 credits per user

**Response:** Array of user profiles with same fields as single user endpoint

### 3.3 Get User Followers

**Endpoint:** `GET /twitter/user/followers`

**Parameters:**
- `userName` (string, required): Twitter username
- `cursor` (string): Pagination cursor, empty for first page

**Response:** Returns 200 followers per page with user profiles in reverse chronological order (newest first)

### 3.4 Get User Followings

**Endpoint:** `GET /twitter/user/followings`

**Parameters:**
- `userName` (string, required): Twitter username
- `cursor` (string): Pagination cursor, empty for first page

**Response:** Returns 200 followed accounts per page with user profiles

### 3.5 Get User Last Tweets

**Endpoint:** `GET /twitter/user/last_tweets`

**Parameters:**
- `userId` (string): User ID (recommended for stability/speed)
- `userName` (string): Twitter username (alternative to userId)
- `includeReplies` (boolean, default: false): Whether to include replies
- `cursor` (string): Pagination cursor, empty for first page

**Response:** Returns up to 20 tweets per page sorted by creation time

### 3.6 Get User Mentions

**Endpoint:** `GET /twitter/user/mentions`

**Parameters:**
- `userName` (string, required): Twitter username
- `sinceTime` (integer): Unix timestamp (seconds) to fetch mentions from
- `untilTime` (integer): Unix timestamp (seconds) to fetch mentions until
- `cursor` (string): Pagination cursor, empty for first page

**Response:** Returns 20 mentions per page in reverse chronological order

## 4. Tweet Endpoints

### 4.1 Get Tweets by IDs

**Endpoint:** `GET /twitter/tweets`

**Parameters:**
- `tweet_ids` (string[], required): Comma-separated list of tweet IDs

**Response:** Array of tweet objects containing:
- id, url, text, source, createdAt, lang, isReply, inReplyToId
- retweetCount, replyCount, likeCount, quoteCount, viewCount
- author object with user details

### 4.2 Get List Tweets

**Endpoint:** `GET /twitter/list/tweets`

**Parameters:**
- `listId` (string, required): The list ID
- `sinceTime` (integer): Unix timestamp to fetch tweets from
- `untilTime` (integer): Unix timestamp to fetch tweets until
- `includeReplies` (boolean, default: true): Whether to include replies
- `cursor` (string): Pagination cursor, empty for first page

**Response:** Returns 20 tweets per page ordered by tweet time (descending)

### 4.3 Get Tweet Replies

**Endpoint:** `GET /twitter/tweet/replies`

**Parameters:**
- `tweetId` (string, required): The tweet ID
- `sinceTime` (integer): Unix timestamp to fetch replies from
- `untilTime` (integer): Unix timestamp to fetch replies until
- `cursor` (string): Pagination cursor, empty for first page

**Response:** Returns 20 replies per page ordered by reply time (descending)

### 4.4 Get Tweet Quotations

**Endpoint:** `GET /twitter/tweet/quotes`

**Parameters:**
- `tweetId` (string, required): The tweet ID
- `sinceTime` (integer): Unix timestamp to fetch quotes from
- `untilTime` (integer): Unix timestamp to fetch quotes until
- `includeReplies` (boolean, default: true): Whether to include replies
- `cursor` (string): Pagination cursor, empty for first page

**Response:** Returns 20 quotes per page ordered by quote time (descending)

### 4.5 Get Tweet Retweeters

**Endpoint:** `GET /twitter/tweet/retweeters`

**Parameters:**
- `tweetId` (string, required): The tweet ID
- `cursor` (string): Pagination cursor, empty for first page

**Response:** Returns about 100 retweeters per page with fields:
- id, userName, url, name, isBlueVerified, profilePicture, coverPicture
- followers, following, createdAt
- has_next_page (boolean) and next_cursor (string) for pagination

### 4.6 Advanced Tweet Search

**Endpoint:** `GET /twitter/tweet/advanced_search`

**Parameters:**
- `query` (string, required): The search query
- `queryType` (enum<string>, required, default: "Latest"): Type of search ("Latest" or "Top")
- `cursor` (string): Pagination cursor, empty for first page

**Search Query Operators:**
- `from:username` - Tweets from a specific user
- `to:username` - Tweets in reply to a specific user
- `OR` - Matches either term (`#AI OR #ML`)
- `AND` - Matches both terms (`#Tesla AND @elonmusk`)
- `-term` - Excludes tweets with the term (`-crypto`)
- `#hashtag` - Matches hashtags
- `@mention` - Mentions of users
- `url:domain` - Tweets containing links
- `since:YYYY-MM-DD_HH:MM:SS_UTC` - Tweets after a date
- `until:YYYY-MM-DD_HH:MM:SS_UTC` - Tweets before a date
- `min_retweets:N` - Minimum retweet count
- `min_faves:N` - Minimum like count
- `min_replies:N` - Minimum reply count
- `filter:media_type` - Filter by media type (images, videos)
- `lang:code` - Filter by language
- `()` - Group operators (`(#AI OR #ML) AND Tesla`)

**Response:** Returns about 20 tweets per page matching the query

## 5. Webhook/Websocket Tweet Filter

### 5.1 Add Webhook/Websocket Tweet Filter Rule

**Endpoint:** `POST /oapi/tweet_filter/add_rule`

**Parameters:**
- `tag` (string, required): Custom tag to identify the rule (max 255 chars)
- `value` (string, required): Rule for filtering tweets (max 255 chars)
- `interval_seconds` (number, required): Interval to check tweets (min: 100, max: 86400)

**Response:**
- `rule_id` (string): ID of the added rule
- `status` (enum<string>): "success" or "error"
- `msg` (string): Error message if applicable

### 5.2 Update Webhook/Websocket Tweet Filter Rule

**Endpoint:** `POST /oapi/tweet_filter/update_rule`

**Parameters:**
- `rule_id` (string, required): ID of the rule to update
- `tag` (string, optional): New custom tag (max 255 chars)
- `value` (string, optional): New filter rule (max 255 chars)
- `interval_seconds` (number, optional): New interval (min: 100, max: 86400)
- `is_activated` (boolean, optional): Whether to activate the rule

**Response:**
- `rule_id` (string): ID of the updated rule
- `status` (enum<string>): "success" or "error"
- `msg` (string): Error message if applicable

### 5.3 Delete Webhook/Websocket Tweet Filter Rule

**Endpoint:** `DELETE /oapi/tweet_filter/delete_rule`

**Parameters:**
- `rule_id` (string, required): ID of the rule to delete

**Response:**
- `status` (enum<string>): "success" or "error"
- `msg` (string): Error message if applicable

### 5.4 Get All Webhook/Websocket Tweet Filter Rules

**Endpoint:** `GET /oapi/tweet_filter/get_rules`

**Response:**
- `rules` (array): List of filter rules with fields:
  - rule_id, tag, value, interval_seconds, is_activated
- `status` (enum<string>): "success" or "error"
- `msg` (string): Error message if applicable

### 5.5 Websocket Connection

**Endpoint:** `wss://api.twitterapi.io/ws/tweet_filter/{rule_id}`

**Headers:**
- `X-API-Key`: Your API key

**Websocket Events:**
- Receives tweets matching the rule in real-time
- Format matches the standard tweet object format

### 5.6 Webhook Registration

**Endpoint:** `POST /oapi/tweet_filter/register_webhook`

**Parameters:**
- `rule_id` (string, required): ID of the rule to connect to webhook
- `webhook_url` (string, required): URL of your webhook endpoint

**Response:**
- `webhook_id` (string): ID of the registered webhook
- `status` (enum<string>): "success" or "error"
- `msg` (string): Error message if applicable

## 6. Common Data Structures

### 6.1 User Object

```json
{
  "id": "1234567890",
  "userName": "johndoe",
  "url": "https://twitter.com/johndoe",
  "name": "John Doe",
  "isBlueVerified": true,
  "profilePicture": "https://pbs.twimg.com/profile_images/...",
  "coverPicture": "https://pbs.twimg.com/profile_banners/...",
  "description": "This is my bio",
  "location": "San Francisco, CA",
  "followers": 1000,
  "following": 500,
  "canDm": true,
  "createdAt": "Thu Dec 13 08:41:26 +0000 2020",
  "fastFollowersCount": 100,
  "favouritesCount": 5000,
  "hasCustomTimelines": true,
  "isTranslator": false,
  "mediaCount": 150,
  "statusesCount": 3000,
  "withheldInCountries": [],
  "possiblySensitive": false,
  "pinnedTweetIds": ["1234567890123456789"],
  "isAutomated": false,
  "automatedBy": null
}
```

### 6.2 Tweet Object

```json
{
  "id": "1234567890123456789",
  "url": "https://twitter.com/username/status/1234567890123456789",
  "text": "This is a tweet",
  "source": "Twitter for iPhone",
  "retweetCount": 50,
  "replyCount": 10,
  "likeCount": 100,
  "quoteCount": 5,
  "viewCount": 1000,
  "createdAt": "Thu Dec 13 08:41:26 +0000 2023",
  "lang": "en",
  "isReply": false,
  "inReplyToId": null,
  "author": {
    "userName": "johndoe",
    "url": "https://twitter.com/johndoe",
    "id": "1234567890",
    "name": "John Doe",
    "isBlueVerified": true,
    "profilePicture": "https://pbs.twimg.com/profile_images/...",
    "coverPicture": "https://pbs.twimg.com/profile_banners/...",
    "description": "This is my bio",
    "followers": 1000,
    "following": 500,
    "createdAt": "Thu Dec 13 08:41:26 +0000 2020"
  },
  "entities": {
    "hashtags": [
      {
        "text": "example",
        "indices": [10, 18]
      }
    ],
    "urls": [
      {
        "url": "https://t.co/abcdefg",
        "expanded_url": "https://example.com",
        "display_url": "example.com",
        "indices": [20, 40]
      }
    ],
    "user_mentions": [
      {
        "screen_name": "janedoe",
        "name": "Jane Doe",
        "id": "9876543210",
        "indices": [0, 8]
      }
    ],
    "media": [
      {
        "id": "1234567890123456789",
        "type": "photo",
        "media_url_https": "https://pbs.twimg.com/media/...",
        "sizes": {
          "small": {"w": 680, "h": 383, "resize": "fit"},
          "large": {"w": 1920, "h": 1080, "resize": "fit"}
        }
      }
    ]
  }
}
```

## 7. Pagination

Most listing endpoints support cursor-based pagination:

1. First request is made with an empty cursor (`""`)
2. Response includes a `next_cursor` value if more results are available
3. Use this `next_cursor` value in subsequent requests to get the next page

## 8. Rate Limits

- Base rate limit of 200 QPS (queries per second) per client
- Some endpoints may have more restrictive limits
- Rate limit headers included in responses:
  - `X-Rate-Limit-Limit`: Maximum requests allowed in the window
  - `X-Rate-Limit-Remaining`: Remaining requests in the current window
  - `X-Rate-Limit-Reset`: Time when the current window resets (UTC epoch seconds)
- Exceeding rate limits results in HTTP 429 responses

## 9. Media Handling

Tweet objects can contain various media types in the `entities` field:

- **Photos**: Available in multiple sizes (small, medium, large)
- **Videos**: Includes duration, aspect ratio, and quality variants
- **GIFs**: Stored as videos with animated_gif type
- **URLs**: Expanded, display, and shortened versions

## 10. Error Handling

- All endpoints return a `status` field ("success" or "error")
- Error responses include a `msg` field with details
- HTTP status codes:
  - 200: Success
  - 400: Bad request (invalid parameters)
  - 401: Authentication error (invalid API key)
  - 403: Permission denied
  - 404: Resource not found
  - 429: Rate limit exceeded
  - 500: Server error

## 11. Sensitive Content Handling

- User objects have a `possiblySensitive` flag
- Tweet search can be filtered with `filter:safe`
- Countries where content is withheld are listed in `withheldInCountries`

## 12. Optimization Tips

1. Use batch endpoints (like `batch_info_by_ids`) to reduce API calls
2. Implement proper cursor-based pagination for large data sets
3. Cache frequently accessed data (user profiles, popular tweets)
4. Use appropriate time filters (`sinceTime`, `untilTime`) to narrow results
5. Implement exponential backoff for rate limiting
6. Choose the right filter rule interval for webhooks/websockets to balance freshness vs. API calls
