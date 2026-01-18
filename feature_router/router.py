from llm.run_agent import run_agent



SCAM_KEYWORDS = ["scam", "fraud", "otp", "phishing","check","link"]


def router_feature(req):
    return run_agent(req)




