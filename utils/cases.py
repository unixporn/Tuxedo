import rethinkdb as r


def update_case(ctx, conn, action_type, explanation):
    user_id = ctx.message.author.id
    case = r.table("cases") \
            .get_all(user_id, index="user_id") \
            .filter({'open': True}) \
            .run()

    if case is None:
        r.table("cases") \
         .insert({
            "user_id": user_id,
            ""
            "open": True,
            "actions": [
                {
                    "type": "open",
                    "explanation": "Case opened"
                }]
            }) \
         .run(conn)

    r.table("cases") \
     .get_all(user_id, index="user_id") \
     .filter({'open': True}) \
     .update({
        "actions": r.row("actions").append({
            "type": action_type,
            "explanation": explanation
            })
        }) \
     .run(conn)

    return
