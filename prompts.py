subective = """I’m a management researcher analyzing shareholder letters and I need your help assessing if a sentence is subjective or if it states objective facts. Markers of subjectivity include words like:

all, no, never, always, but, not, if, or, know, know, how, think, feel, how, because, make, why, believe, would, can, want, could, if, or, any, something, really, actually, of course, real, but, not, if, or

Sentences that contain those words may not be subjective, but the presence of those words may indicate that subjectivity. If the text I show you is subjective, output the number 1, otherwise output 0. Most sentences won’t contain any subjectivity, so you must return 0. Only output this number. 

I believe our new initiative will bring transformative changes to the industry.
1

We think innovation is the real key to our success
1

"""
visionary = """I’m a management researcher analyzing shareholder letters and I need your help assessing if part of a shareholder letter is attempting to influence its readers by providing insights into the company’s future aspirations, plans, or anticipations. Markers of visionary perspective include words like:

will, going to, have to, may

Sentences that contain those words may not be providing a visionary perspective, but the presence of those words may indicate that. If the text contains this, output the number 1, otherwise output 0. Most sentences won’t contain visionary perspective, so you must return 0. Only output this number. 

In the next decade, we envision our company at the forefront of sustainable innovations.
1

By 2030, we aspire to be the global leader in sustainable energy solutions, driving a greener future for all.
1

"""

reframing = """I’m a management researcher analyzing shareholder letters and I need your help assessing if part of a shareholder letter is attempting to influence its readers by “reframing”. “Reframing” is conveying a positive outlook on current or future endeavors, or the company's direction, especially as they mention setbacks. Markers of reframing include words like:

Alternatively
Otherwise
Rather
Instead
in comparison
by comparison
more accurately
more precisely
on the other hand
in contrast
by contrast
on the contrary
admittedly
anyway
besides
however
nevertheless
nonetheless
after all
all the same
at any rate
at the same time
for all that
in any case
in any event
in spite of that
of course
on the other hand
that said

Sentences that are reframing should include at least one concessive or contrast adjunct expression like in the list above. If the text contains reframing, output the number 1, otherwise output 0. Most sentences won’t contain reframing, so you must return 0. Only output this number.

Despite the challenges we’ve faced, our team’s resilience assures me that brighter days lie ahead.
1

Every challenge we’ve faced has only reinforced our belief that brighter days are just around the corner
1

"""

stakeholder = """I’m a management researcher analyzing shareholder letters and I need your help assessing if part of a shareholder letter is attempting to influence its readers by using stakeholder engagement. Stakeholder engagement is when the text actively engages or calls upon stakeholders (like employees, customers, and shareholders) to participate, believe in, or support the company’s direction. Markers of stakeholder engagement includes words like:

shareholders, employees, clients/customers, supplier, government, medias

Sentences that contain those words may not have stakeholder engagement, but the presence of those words may indicate that. If the text contains this, output the number 1, otherwise output 0. Most sentences won’t contain stakeholder engagement, so you must return 0. Only output this number. 

Together, with our dedicated employees and loyal customers, we can shape a more sustainable future.
1

To our dedicated team members and loyal customers, your unwavering commitment is the bedrock upon which our success is built; let’s continue this journey together.
1



"""

emotion = """I’m a management researcher analyzing shareholder letters and I need your help assessing if part of a shareholder letter is attempting to influence its readers with positive emotional appeal. Positive emotional appeal is when the text employs positive emotional language or stories to elicit positive emotions from the audience. Markers of emotional appeal includes words like:

good, love, happy, hope

Sentences that contain those words may not have positive emotional appeal, but the presence of those words may indicate that. If the text contains this, output the number 1, otherwise output 0. Most sentences won’t contain positive emotional appeal, so you must return 0. Only output this number.

Every milestone we achieved this year filled our hearts with gratitude and renewed determination.
1

The trust you place in us brings a profound sense of responsibility and pride, driving us to reach greater heights.
1

"""
