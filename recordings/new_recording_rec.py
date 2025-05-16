from seleniumbase import BaseCase
BaseCase.main(__name__, __file__)


class RecorderTest(BaseCase):
    def test_recording(self):
        # self.open("https://infolegale.ilucca.net/directory/users/cards")
        # self.open("https://infolegale.ilucca.net/api/v3/users/scope?appInstanceId=14&operations=1&fields=id,name,firstName,lastName,mail,directLine,professionalMobile,jobTitle,birthDate,picture[id,name,url,href,mimetype],collection.count&orderBy=lastName,asc&paging=0,200")
        # self.open("https://infolegale.ilucca.net/directory/users/cards?employeeId=223")
        # self.click("div.json-formatter-container")
        # self.open("https://infolegale.ilucca.net/directory/users/cards?employeeId=39")
        # self.click("body pre")
        # self.click("div.businesscard-content-wrapper div:nth-of-type(3) p")
        # self.open("https://infolegale.ilucca.net/directory/users/cards?employeeId=39")
        # self.open("https://infolegale.ilucca.net/api/v3/users?id=39&fields=id,firstName,lastName,picture[id,name,href],jobTitle,department[name,id],legalEntity[name],dtContractStart,mail,manager[id,name,firstName,lastName,picture[id,name,href]],directLine,professionalMobile,birthDate")
        # self.click("div.json-formatter-container")
        self.open("https://infolegale.ilucca.net/api/v3/users?id=223&fields=id,firstName,lastName,picture[id,name,href],jobTitle,department[name,id],legalEntity[name],dtContractStart,mail,manager[id,name,firstName,lastName,picture[id,name,href]],directLine,professionalMobile,birthDate")
        # self.click("div.json-formatter-container")
