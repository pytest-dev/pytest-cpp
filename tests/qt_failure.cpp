#include <QtTest/QtTest>

class TestFailure: public QObject
{
    Q_OBJECT
private slots:
    void TestFailureOne();
    void TestFailureTwo();
};

void TestFailure::TestFailureOne()
{
       QCOMPARE(2 * 3, 5);
}

void TestFailure::TestFailureTwo()
{
       QCOMPARE(2 - 1, 0);
}

QTEST_MAIN(TestFailure)
#include "qt_failure.moc"
