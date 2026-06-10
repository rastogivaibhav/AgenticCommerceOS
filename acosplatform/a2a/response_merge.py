def merge_responses(responses, channel_mode='customer_direct'):
    body=' '.join(r.get('response','') for r in responses)
    if channel_mode=='customer_direct': prefix='Here is the best John Lewis guidance: '
    elif channel_mode=='store_partner_assist': prefix='Partner assist summary: '
    elif channel_mode=='contact_centre_assist': prefix='Contact-centre safe summary: '
    else: prefix='Internal orchestration summary: '
    return prefix + body
