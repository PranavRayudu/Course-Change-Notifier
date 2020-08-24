import React from 'react';
import {Space, Card} from "antd";

function NotFound() {
    return <Card bordered={false}>
        <Space direction={"vertical"} style={{width: "100%"}}>
            <h1 style={{textAlign: "center"}}>404 Page Not Found</h1>
        </Space>
    </Card>
}

export default NotFound;


