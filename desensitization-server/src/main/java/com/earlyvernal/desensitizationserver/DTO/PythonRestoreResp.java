package com.earlyvernal.desensitizationserver.DTO;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
public class PythonRestoreResp {

    private List<Item>results;

    @Data
    public static class Item{
        private String filename;
        private Boolean ok;

        @JsonProperty("image_base64")
        private String imageBase64;

        private String error;
    }
}
