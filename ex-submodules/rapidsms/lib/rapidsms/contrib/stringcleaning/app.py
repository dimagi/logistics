import rapidsms
import re

class App (rapidsms.App):

    def parse (self, message):
        ''' Cleans up messages by removing punctuation, and replacing intended
        numbers with numerals, for example:

        original: "hello"., 2lli.o .2.o.i. d.s. 12.1. 'l3oii user4' "o0,oo", o0.oo,"o0. oo", oo0. ooo0"
        shiny new: hello 2111.0 2.0.1 ds 12.1 13011 user4 00 oo 00.00 00 oo 000 ooo0'''

        # dont mess with the real message text until the end
        msgtxt = message.text

        # remove leading/trailing whitespace
        # get out your featherduster
        msgtxt = msgtxt.strip()

        # replace separation marks with a space
        separators = [',', '/', ';', '*', '+', '-']
        for mark in separators:
                msgtxt = msgtxt.replace(mark, ' ')

        # remove other marks (we'll deal with . later)
        junk = ['\'', '\"', '`', '(', ')']
        for mark in junk:
            msgtxt = msgtxt.replace(mark, '')

        #remove trailing period (.)
        if msgtxt[-1:] == '.':
            msgtxt = msgtxt[:-1]

        # split the text into chunks
        blobs = msgtxt.split(" ")
        clean_blobs = []
        for blob in blobs:
            clean_blob = blob
            for n in range(3):
                # clean up blobs only if they have a digit in the first few
                # characters -- so we don't clean up things like user1
                try:
                    if blob[n].isdigit():
                        clean_blob = self.letters_for_numbers(blob)
                        break
                except IndexError:
                    # if the blob doesnt have the first few characters,
                    # and there is no digit yet, move on
                    break
            # add the cleaned blob (or untouched blob) to a running list
            clean_blobs.append(clean_blob)

        # reconstruct msgtxt with clean blobs
        msgtxt = " ".join(clean_blobs)

        # remove periods, keep decimal points
        msgtxt = self.period_vs_decimal(msgtxt)

        self.info("string cleaning! featherduster!")
        self.info("original: " + message.text)
        self.info("shiny new: " + msgtxt)

        # give the message clean text
        message.text = msgtxt


    def period_vs_decimal(self, str):
        '''Removes .'s unless they are between two digits'''
        txt = str
        # marker for wayfinding within the string
        marker = 0
        for p in range(txt.count('.')):

            # move the marker to each . by adding the previous marker to the
            # location of the next . within the substring beyond the marker
            marker = marker + txt[marker:].index('.')

            if txt[marker-1].isdigit() and txt[marker + 1].isdigit():
                # if the . is between two digits, move the marker to the
                # next character and find another .
                marker += 1
                continue
            else:
                # save the slice up to and the slice beyond this . and move on
                # (leave out the .)
                txt = txt[:marker] + txt[marker + 1:]
                marker += 1
        return txt


    def letters_for_numbers(self, str):
        # dict of letters and the numerals they are intended to be
        gaffes = {'i': '1', 'l': '1', 'o': '0'}

        # don't worry about case
        numeralized = str.lower()

        for g in gaffes.iterkeys():
            try:
                # replace each of the letters with its appropriate numeral
                numeralized = numeralized.replace(g, gaffes[g])
            except Exception, e:
                print e
        # return the string once all gaffes have been replaced
        return numeralized