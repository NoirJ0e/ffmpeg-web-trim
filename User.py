class User:
    def __init__(self, email, hashed_password, edit_record) -> None:
        self.email = email
        self.hashed_password = hashed_password
        self.records = [edit_record]
    @property
    def email(self):
        return self._email
    @property
    def hashed_password(self):
        return self._hashed_password
    @property
    def records(self):
        return self._records
    def add_record(self, edit_record):
        self.records.append(edit_record)