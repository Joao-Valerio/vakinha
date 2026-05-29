from typing import Any, Dict


def resolve_reply_jid(key_data: Dict[str, Any]) -> str:
    """
    Resolves the best JID/identifier to reply to (Evolution / WhatsApp).
    Handles @s.whatsapp.net, @lid, remoteJidAlt and senderPn.
    """
    remote_jid = (key_data.get("remoteJid") or "").strip()
    remote_jid_alt = (key_data.get("remoteJidAlt") or "").strip()
    sender_pn = (key_data.get("senderPn") or "").strip()

    if remote_jid.endswith("@s.whatsapp.net"):
        return remote_jid
    if remote_jid_alt.endswith("@s.whatsapp.net"):
        return remote_jid_alt
    if sender_pn:
        if "@" in sender_pn:
            return sender_pn
        digits = sender_pn.lstrip("+").replace(" ", "")
        if digits:
            return f"{digits}@s.whatsapp.net"
    if remote_jid:
        return remote_jid
    return remote_jid_alt
