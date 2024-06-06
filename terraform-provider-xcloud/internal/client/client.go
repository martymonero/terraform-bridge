package client

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/hashicorp/terraform-plugin-log/tflog"
)

type Client struct {
	client        *http.Client
	endpoint      string
	token         string
	version       string
	poll_interval time.Duration
}

type Server struct {
	Id          int64      `json:"id,omitempty"`
	Name        string     `json:"name"`
	Image       Image      `json:"image"`
	ServerType  ServerType `json:"server_type"`
	Datacenter  Datacenter `json:"datacenter"`
	Ipv4Address string     `json:"ipv4_address,omitempty"`
}

type ServerCreateResponse struct {
	Action Action `json:"action"`
	Server Server `json:"server"`
}

type ServerGetResponse struct {
	Server Server `json:"server"`
}

type DeleteResponse struct {
	Action Action `json:"action"`
}

type Image struct {
	Id   int64  `json:"id,omitempty"`
	Name string `json:"name"`
}

type ServerType struct {
	Id   int64  `json:"id,omitempty"`
	Name string `json:"name"`
}

type Datacenter struct {
	Id   int64  `json:"id,omitempty"`
	Name string `json:"name"`
}

type Action struct {
	Id         int64  `json:"id"`
	Command    string `json:"command"`
	Status     string `json:"status"`
	IsFinished bool   `json:"is_finished"`
}

type ActionGetResponse struct {
	Action Action `json:"action"`
}

type ActionListResponse struct {
	Actions []Action `json:"actions"`
}

func New(endpoint string, token string, poll_interval_string string, version string) (*Client, error) {
	poll_interval, err := time.ParseDuration(poll_interval_string)

	if err != nil {
		poll_interval, _ = time.ParseDuration("500ms")
	}

	c := Client{
		client:        &http.Client{Timeout: 30 * time.Second},
		endpoint:      endpoint,
		token:         token,
		poll_interval: poll_interval,
		version:       version,
	}

	return &c, nil
}

func (c *Client) GetAction(actionId int64) (*Action, error) {

	req, err := http.NewRequest("GET", fmt.Sprintf("%s/actions/%d", c.endpoint, actionId), nil)
	if err != nil {
		return nil, err
	}

	body, err := c.doRequest(req)
	if err != nil {
		return nil, err
	}

	actionGetResponse := ActionGetResponse{}

	err = json.Unmarshal(body, &actionGetResponse)
	if err != nil {
		return nil, err
	}

	return &actionGetResponse.Action, nil

}

func (c *Client) GetServer(serverId int64) (*Server, error) {

	req, err := http.NewRequest("GET", fmt.Sprintf("%s/servers/%d", c.endpoint, serverId), nil)
	if err != nil {
		return nil, err
	}

	body, err := c.doRequest(req)
	if err != nil {
		return nil, err
	}

	serverGetResponse := ServerGetResponse{}

	err = json.Unmarshal(body, &serverGetResponse)
	if err != nil {
		return nil, err
	}

	return &serverGetResponse.Server, nil

}

func (c *Client) CreateServer(server Server) (*Server, error) {
	rb, err := json.Marshal(server)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/servers", c.endpoint), strings.NewReader(string(rb)))
	if err != nil {
		return nil, err
	}

	body, err := c.doRequest(req)
	if err != nil {
		return nil, err
	}

	newServerCreateResponse := ServerCreateResponse{}
	err = json.Unmarshal(body, &newServerCreateResponse)
	if err != nil {
		return nil, err
	}

	for {
		time.Sleep(c.poll_interval)

		action, err := c.GetAction(newServerCreateResponse.Action.Id)

		if err != nil {
			return nil, err
		}

		if action.IsFinished {
			break
		}
	}

	finalServer, err := c.GetServer(newServerCreateResponse.Server.Id)

	if err != nil {
		return nil, err
	}

	return finalServer, nil

}

func (c *Client) DeleteServer(ctx context.Context, serverId int) error {

	req, err := http.NewRequest("DELETE", fmt.Sprintf("%s/servers/%d", c.endpoint, serverId), nil)

	if err != nil {
		return err
	}

	body, err := c.doRequest(req)
	if err != nil {
		return err
	}

	newServerDeleteResponse := DeleteResponse{}
	err = json.Unmarshal(body, &newServerDeleteResponse)
	if err != nil {
		return err
	}

	for {
		time.Sleep(c.poll_interval)

		action, err := c.GetAction(newServerDeleteResponse.Action.Id)

		if err != nil {
			return err
		}

		if action.IsFinished {
			break
		}

		tflog.Info(ctx, "action still running...")
	}

	return nil

}

func (c *Client) doRequest(req *http.Request) ([]byte, error) {
	req.Header.Add("Authorization", "Bearer "+c.token)

	if req.Method == http.MethodPost || req.Method == http.MethodPut || req.Method == http.MethodPatch {
		req.Header.Add("Content-Type", "application/json")
	}

	req.Header.Add("User-Agent", "xcloud-terraform/"+c.version)

	res, err := c.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}

	if res.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("status: %d, body: %s", res.StatusCode, body)
	}

	return body, err
}
