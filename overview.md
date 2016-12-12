### Overview

_Context: This is an example of a real-life project we built & deployed recently. If you're seeing this, it means we'd like to see how you would solve a similar problem and we think take-home projects are more fun when they are concrete and domain-specific rather than generic throwaway projects. But to be totally clear, we won't be using your code for anything beyond deciding on moving forward in the hiring process._

Users in Close.io can make/receive unlimited phone calls to any phone number in the world, for one monthly price. This is mostly true, except that some areas are so absurdly expensive that we have to block calling to very remote places and exceptionally expensive number prefixes. Free trial users also get access to unlimited international calling, except we restrict it a bit further to avoid high costs and abuse.

So far the above logic has been enforced through hardcoded data in a file we call `phone.py`. Attached is a shortened version of this file/data. When a phone call is attempted, we simply check it against `is_restricted_number` and return an error message if necessary.

We'd like to improve this in the following ways:

- Move all of the prefix data into a database so we don't have to deploy code changes on every tweak.
- We'd like the ability to block an overall country code (blacklist prefix) but whitelist a specific phone number or prefix within that country code.
- The prefix data from `phone.py` data should be the default, however we'd like the ability to change the whitelist _or_ blacklist data for a specific organization. For example, we typically want to blacklist calling to the Bahamas for trial users/organizations, but for a specific large potential customer we want to relax/disable this restriction for them. Note that 98% of organizations will not have any special rules applied, however.

Requirements:

- Write a Python (2 or 3) app that we can easily plug in to our main Flask app to replace `is_restricted_number`. It should take an additional parameter now (`organization_id` of the user).
- Provide a script we can run one-time to populate the database from `phone.py` data.
- It should be well unit tested so we can tell the whitelist/blacklist/per-organization/trial overrides work well.
- The prefix data should be stored persistently in a data store.
- You can see a similar project called [flask-ipblock](https://github.com/closeio/flask-ipblock) but the logic and requirements are a bit different of course (e.g. phone numbers are prefix based vs. based on fixed length numbers).
- You don't need to create any web UI for actually adding/updating the data, but do add any helper methods that would be useful for someone who was making an admin interface to CRUD the data.
- **Make it as fast as you can** since this operation is in the middle of a flow that a user performs hundreds of times per day.
- Don't cache the rules/data in the application layer since that would make it more complex to propagate rule changes instantly. Instead, store the rules in the database and either perform the "check" in the database, or only fetch what's needed to perform that one check application-side.
- Data store: Use Redis (you can treat as persistent), MongoDB, Postgres, or MySQL
- (Optional/Bonus) For performance reasons, we recommend using Redis both for storage and also for calculations (e.g. with a Lua script), however we'll be happy with a fast MongoDB/Postgres/MySQL-only solution too.
- Your solution will be graded on functionality, completeness, unit tests, documentation, cleanliness, and code structure.

Please don't make this problem or project public. To submit your code, just email it back to us.
