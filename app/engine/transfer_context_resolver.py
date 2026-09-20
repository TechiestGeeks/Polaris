from app.models.schemas import ParsedContext

class TransferContextResolver:
    @staticmethod
    def resolve(context: ParsedContext, question: str) -> ParsedContext:
        """
        Explicitly distinguishes between internal and external data sharing
        based on explicit external signals, rather than defaulting to external.
        """
        if context.intent == "DATA_SHARING":
            # List of hardcoded keywords that strongly indicate external sharing
            keywords = ["external vendor", "third party", "outside", "customer", "partner", "supplier", "vendor", "externally"]
            question_lower = question.lower()
            has_external_keyword = any(k in question_lower for k in keywords)
            
            is_external = context.explicit_external_signal or has_external_keyword or bool(context.vendor)
            
            if is_external:
                context.sharing_type = "EXTERNAL"
                context.action = "EXTERNAL_SHARE"
                context.external_party = True
            else:
                context.sharing_type = "INTERNAL"
                context.action = "INTERNAL_SHARE"
                context.external_party = False
                
        return context
