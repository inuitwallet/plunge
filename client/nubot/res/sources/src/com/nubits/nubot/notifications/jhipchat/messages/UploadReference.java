/*
 * Copyright 2012 Nick Campion < campnic at gmail.com >
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.nubits.nubot.notifications.jhipchat.messages;

public class UploadReference {

    private String name;
    private Integer size;
    private String url;

    private UploadReference() {
        // nothing
    }

    public String getName() {
        return name;
    }

    public Integer getSize() {
        return size;
    }

    public String getUrl() {
        return url;
    }

    static UploadReference create(String name, Integer size, String url) {
        UploadReference ref = new UploadReference();
        ref.name = name;
        ref.size = size;
        ref.url = url;
        return ref;
    }
}
