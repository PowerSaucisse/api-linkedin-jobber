import falcon, psycopg2, os, urllib

CONN = None

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME", "jobber")
DB_USER = os.getenv("DB_USER", "beehavior")
DB_PASS = os.getenv("DB_PASS", "beehavior")
API_SECRET = os.getenv("API_SECRET", "1312-ACAB")

def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        password=DB_PASS,
        user=DB_USER,
        dbname=DB_NAME
    )

class AuthorizeAccess:
    def __call__(self, req, resp, resource, params):
        if req.auth == API_SECRET:
            return
        else:
            raise falcon.HTTPUnauthorized(title="UNAUTHORIZED", description="You don't have access to this resource")


class AccountResource:

    @falcon.before(AuthorizeAccess())
    def on_post(self, req, resp):
        conn = get_db()
        name = req.media["name"]
        link = req.media["link"]
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO accounts (name, link) VALUES (%s, %s)", (name, link))
                conn.commit()
        except:
            conn.rollback()

        resp.status = falcon.HTTP_201
        resp.media = {"title": "CREATED", "description": "Linkedin account added"}

    @falcon.before(AuthorizeAccess())
    def on_get(self, req, resp):
        conn = get_db()
        q1 = None
        with conn.cursor() as cur:
            cur.execute("SELECT name, link, spammed_on FROM accounts")
            q1 = cur.fetchall()
        
        content: list = []
        for x in q1:
            content.append({
                "name": x[0],
                "link": x[1],
                "spammed_on": None if x[2] is None else str(x[2])
            })
        
        resp.status = falcon.HTTP_200
        resp.media = {
            "title": "OK", 
            "description": "Linkedin account getted",
            "content": {
                "num": len(content),
                "accounts": content
            }
        }

    @falcon.before(AuthorizeAccess())
    def on_put(self, req, resp):
        link_id = urllib.parse.quote(req.get_param("link_id"))
        conn = get_db()
        print("stage #1")
        print(link_id)
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE accounts SET spammed_on = (NOW() AT TIME ZONE 'utc') WHERE link = %s", (link_id,))
                print("stage #2")
                conn.commit()
        except Exception as e:
            print(f'stage #3, error : {e}')
            conn.rollback()
            raise falcon.HTTPBadRequest()

        resp.status = falcon.HTTP_200
        resp.media = {"title": "UPDATED", "description": "Linkedin account spam updated"}


api = falcon.App()
api.add_route("/api/service/jobber/account", AccountResource())