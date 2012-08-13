# -*- encoding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from bs4 import BeautifulSoup
import re
import urllib2

URL = 'http://www.infojobs.net/ofertas-trabajo/informatica-telecomunicaciones/'


class Offer(object):
    def __init__(self):
        self.date = ''
        self.vacant = ''
        self.number_of_vacants = 0
        self.poblation = ''
        self.company = ''
        self.company_cid = ''
        self.url = ''
        self.level = ''
        self.description = ''
        self.min_form = ''
        self.min_exp = ''
        self.min_req = ''
        self.des_req = ''
        self.salary = 0


class IJParser(object):
    def __init__(self, parser, markup=None, pages_limit=1):
        self.parser = parser
        self.markup = markup
        self.url = URL

        print '>>>> URL: %s' % URL

        self.poblations = set()
        self.banners = set()
        self.companies = dict()
        self.premium_offers = list()
        self.standard_offers = list()
        self.pages_limit = pages_limit

        self.fetch()

    def fetch(self):
        orig_url = self.url
        i = 1

        while i <= self.pages_limit:
            self.url = self.url + '%s' % i
            print '>>>> [%s of %s] >> Processing: %s' % (i, self.pages_limit,
                self.url)

            self._get_offers_()
            self._get_banners_()
            self.url = orig_url
            i = i + 1

        self.get_detail()

    def _get_offers_(self):
        #table_results_highlighted = soup.body.find_all(
        #    id='table_results_destacadas')
        soup = self.get_soup()
        tables = soup.body.find_all('table')

        if len(tables) == 1:
            standard_offers = self.parse_offer(tables[0])
            self.standard_offers.extend(standard_offers)
        else:
            premium_offers = self.parse_offer(tables[0])
            self.premium_offers.extend(premium_offers)

            standard_offers = self.parse_offer(tables[1])
            self.standard_offers.extend(standard_offers)

    def _get_banners_(self):
        soup = self.get_soup()
        hidden_div = soup.body.find_all(id=re.compile('^Hidden_stag_x'))
        banners = set()
        for div in hidden_div:
            a = div.a
            if a:
                img = a.img
                if img:
                    src = img['src']
                    if src:
                        url = 'http://%s' % src[2:len(src)]
                        banners.add(url)
        self.banners.update(banners)

    def parse_offer(self, data):
        offers = list()

        if data:
            tr_list = data.find_all('tr')
            if tr_list:
                for tr in tr_list:
                    columns = tr.find_all('td')
                    offer = self.get_offers_from(columns)
                    if offer:
                        offers.append(offer)
        return offers

    def get_offers_from(self, columns):
        offer = {}

        for column in columns:
            if not column.string:
                class_td = column['class'][0]
                if 'vacant' == class_td:
                    v = column.find_all('div', attrs={'class': 'cell-text'})[0]
                    if v:
                        a = v.a
                        if a:
                            href = a['href']
                            vacant = a.text.strip().title()
                            elem = dict(
                                        link=href,
                                        name=vacant
                                       )

                            offer.update({'vacant': elem})
                if 'poblation' == class_td:
                    p = column.find_all('div', attrs={'class': 'cell-text'})[0]
                    if p:
                        poblation = p.text.strip().title()
                        offer.update({'poblation': poblation})
                        self.poblations.add(offer['poblation'])
                if 'company' == class_td:
                    c = column.find_all('div', attrs={'class': 'cell-text'})[0]
                    if c:
                        a = c.a
                        if a:
                            href = a['href']
                            cid = href.strip().lower().replace('/', '.')\
                                .replace('-', '.')
                            c_name = a.text.strip().title()
                            elem = {c_name: dict(cid=cid, link=href,
                                name=c_name)}
                            offer.update({'company': c_name, 'cid': cid})
                            self.companies.update(elem)
                if 'date' == class_td:
                    p = column.find_all('div', attrs={'class': 'cell-text'})[0]
                    if p:
                        pub_date = p.text.strip()
                        if pub_date:
                            offer.update({'date': pub_date})

        if 'poblation' in offer.keys() and 'vacant' in offer.keys() \
            and 'date' in offer.keys():
            ooffer = Offer()
            ooffer.url = offer['vacant']['link']
            ooffer.vacant = offer['vacant']['name']
            ooffer.date = offer['date']
            ooffer.poblation = offer['poblation']
            ooffer.company = offer['company']
            ooffer.company_cid = offer['cid']
            return ooffer
        else:
            return None

    def get_detail(self):
        all_offers = self.premium_offers + self.standard_offers
        total = len(all_offers)

        for index, offer in enumerate(all_offers):
            self.url = 'http:%s' % offer.url
            print '>>>> [%s of %s] >> Processing: %s' % (index + 1, total,
                self.url)
            soup = self.get_soup()

            tables = soup.find_all("table", {"class": "DatosTabulados"})

            description = tables[2]
            prefijoNivelLaboral = description.find_all('td',
                {"id": "prefijoNivelLaboral"})
            prefijoVacantes = description.find_all('td',
                {"id": "prefijoVacantes"})
            prefijoDescripcion1 = description.find_all('td',
                {"id": "prefijoDescripcion1"})

            if prefijoNivelLaboral and len(prefijoNivelLaboral) > 0:
                nivelLaboral = prefijoNivelLaboral[0]
                if nivelLaboral:
                    offer.level = nivelLaboral.text.strip()

            if prefijoVacantes and len(prefijoVacantes) > 0:
                vacantes = prefijoVacantes[0]
                if vacantes:
                    offer.number_of_vacants = vacantes.text.strip()

            if prefijoDescripcion1 and len(prefijoDescripcion1) > 0:
                descripcion1 = prefijoDescripcion1[0]
                if descripcion1:
                    offer.description = descripcion1.text.strip()

            requirements = tables[3]
            prefijoEstMin = requirements.find_all('td',
                {"id": "prefijoEstMin"})
            prefijoExpMin = requirements.find_all('td',
                {"id": "prefijoExpMin"})
            prefijoReqMinimos = requirements.find_all('td',
                {"id": "prefijoReqMinimos"})
            prefijoReqDeseados = requirements.find_all('td',
                {"id": "prefijoReqDeseados"})

            if prefijoEstMin and len(prefijoEstMin) > 0:
                estMin = prefijoEstMin[0]
                if estMin:
                    offer.min_form = estMin.text.strip()

            if prefijoExpMin and len(prefijoExpMin) > 0:
                expMin = prefijoExpMin[0]
                if expMin:
                    offer.min_exp = expMin.text.strip()

            if prefijoReqMinimos and len(prefijoReqMinimos) > 0:
                reqMinimos = prefijoReqMinimos[0]
                if reqMinimos:
                    offer.min_req = reqMinimos.text.strip()

            if prefijoReqDeseados and len(prefijoReqDeseados) > 0:
                reqDeseados = prefijoReqDeseados[0]
                if reqDeseados:
                    offer.des_req = reqDeseados.text.strip()

            salary = tables[4]
            prefijoSalario = salary.find_all('td', {"id": "prefijoSalario"})

            if prefijoSalario and len(prefijoSalario) > 0:
                salario = prefijoSalario[0]
                if salario:
                    offer.salary = salario.text.strip()

    def get_soup(self):
        default_user_agent = "Mozilla/5.0 (X11; Linux x86_64)" +\
            " AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.121" +\
            " Safari/535.2"
        headers = {'User-Agent': default_user_agent}
        req = urllib2.Request(self.url, None, headers)
        response = urllib2.urlopen(req)
        html = response.read()
        soup = BeautifulSoup(html, self.parser)

        return soup


def fetch():
    IJParser('lxml', pages_limit=1)


def main():
    import timeit

    print '*' * 80

    funcs_to_measure = (
        ('>>>> executing fetch...', timeit.Timer(fetch)),
    )

    for func_to_measure in funcs_to_measure:
        try:
            print func_to_measure[0]
            print '     >>>> Total exec. time: %s'\
                % func_to_measure[1].timeit(1)
            print '*' * 80
        except:
            func_to_measure[1].print_exc()


if __name__ == "__main__":
    main()
