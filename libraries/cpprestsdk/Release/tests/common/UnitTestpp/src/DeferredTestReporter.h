/***
* This file is based on or incorporates material from the UnitTest++ r30 open source project.
* Microsoft is not the original author of this code but has modified it and is licensing the code under 
* the MIT License. Microsoft reserves all other rights not expressly granted under the MIT License, 
* whether by implication, estoppel or otherwise. 
*
* UnitTest++ r30 
*
* Copyright (c) 2006 Noel Llopis and Charles Nicholson
* Portions Copyright (c) Microsoft Corporation
*
* All Rights Reserved.
*
* MIT License
*
* Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
* and associated documentation files (the "Software"), to deal in the Software without restriction, 
* including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
* and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, 
* subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in all copies or 
* substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
* INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE 
* AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
* DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
***/

#ifndef UNITTEST_DEFERREDTESTREPORTER_H
#define UNITTEST_DEFERREDTESTREPORTER_H

#include "../config.h"

#ifndef UNITTEST_NO_DEFERRED_REPORTER

#include "TestReporter.h"
#include "DeferredTestResult.h"

#include <vector>

namespace UnitTest
{

class DeferredTestReporter : public TestReporter
{
public:
    UNITTEST_LINKAGE virtual void ReportTestStart(TestDetails const& details);
    UNITTEST_LINKAGE virtual void ReportFailure(TestDetails const& details, char const* failure);
    UNITTEST_LINKAGE virtual void ReportTestFinish(TestDetails const& details, bool passed, float secondsElapsed);

    typedef std::vector< DeferredTestResult > DeferredTestResultList;
    UNITTEST_LINKAGE DeferredTestResultList& GetResults();

private:
    DeferredTestResultList m_results;
};

}

#endif
#endif
