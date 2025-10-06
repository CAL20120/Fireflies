class test:
    def __init__(self):
        super(test, self).__init__()
    
    def test_print(self):
        print("coucou")


from fireflies.fireflies_utils.test.test_print import test

x = test()
x.test_print()